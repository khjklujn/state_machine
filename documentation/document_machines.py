# standard library imports
import os
from pprint import pprint
import shutil
import sys

sys.path.append("../long_term_storage")

# third party imports
from graphviz import Digraph

# application imports
from service.backup.backup_and_encrypt import MachineBackupAndEncrypt
from service.backup.backup_databases import MachineBackupDatabases
from service.create_client.create_client import (
    MachineCreateClient,
)
from service.create_client.validate import MachineValidate
from service.decrypt.decryption import (
    MachineDecryption as DecryptMachineDecryption,
)
from service.decrypt.validation import (
    MachineValidation as DecryptMachineValidation,
)
from service.dynamic_mount import MachineDynamicMount
from service.restore.decryption import MachineDecryption
from service.restore.restoration import MachineRestoration
from service.restore.validation import MachineValidation
from service.retention_end_of_month.eom_delete import MachineEomDelete
from service.retention_end_of_month.eom_deletion_candidates import (
    MachineEomDeletionCandidates,
)
from service.retention_end_of_year.eoy_delete import MachineEoyDelete
from service.retention_end_of_year.eoy_deletion_candidates import (
    MachineEoyDeletionCandidates,
)
from service.archive_encrypted.archive_encrypted_machine import (
    MachineArchiveEncrypted,
)
from state_machine import AbstractMachine


def generate_svg(cls: type[AbstractMachine], path: str):
    """
    Generates an SVG diagram of the state-machine.
    """

    class_name = cls.__module__.split(".")[-1]

    dot = Digraph(name=class_name)
    all_nodes = cls.__entry_nodes__ + cls.__nodes__ + cls.__terminal_nodes__
    cluster_index = 0
    for node in all_nodes:
        node_name = node.__node_name__.split(".")[-1]
        if node.__is_entry__:
            color = "orange"
            shape = "doubleoctagon"
        elif node.__is_terminal__:
            color = "yellow"
            shape = "doubleoctagon"
        else:
            color = "lightblue"
            shape = "ellipse"

        if node.__invokes_machine__:
            with dot.subgraph(  # pyright: ignore[reportOptionalContextManager]
                name=f"cluster{cluster_index}"
            ) as machine:
                machine.attr(color="blue")
                machine.node(
                    node_name,
                    fillcolor=color,
                    style="filled",
                    shape=shape,
                    tooltip=node.__overview__,
                )
                machine.attr(label=node.__invokes_machine__)
                cluster_index += 1
        else:
            dot.node(
                node_name,
                fillcolor=color,
                style="filled",
                shape=shape,
                tooltip=node.__overview__,
            )

        for exit_node in node.__happy_paths__:
            exit_name = exit_node.split(".")[-1]
            dot.edge(node_name, exit_name, color="green")

        for exit_node in node.__unhappy_paths__:
            exit_name = exit_node.split(".")[-1]
            dot.edge(node_name, exit_name, color="red")

    print("dot", os.path.join(path, class_name))
    dot.render(format="svg", filename=os.path.join(path, class_name))
    os.remove(os.path.join(path, class_name))


machines = (
    MachineBackupAndEncrypt,
    MachineBackupDatabases,
    MachineCreateClient,
    DecryptMachineValidation,
    DecryptMachineDecryption,
    MachineValidate,
    MachineDynamicMount,
    MachineDecryption,
    MachineRestoration,
    MachineValidation,
    MachineEomDelete,
    MachineEomDeletionCandidates,
    MachineEoyDelete,
    MachineEoyDeletionCandidates,
    MachineArchiveEncrypted,
)

root = "./documentation/docs/machine_diagrams"

if os.path.exists(root):
    shutil.rmtree(root)

for machine in machines:
    path = machine.__module__.split(".")
    machine_name = path[-1]
    machine_path = os.path.join(root, *path[2:])
    os.makedirs(machine_path, exist_ok=True)
    generate_svg(machine, machine_path)

    md_file = os.path.join(machine_path, f"{machine_name}.md")
    machine_class = "".join([word.capitalize() for word in machine_name.split("_")])
    print(md_file)
    with open(md_file, "w") as file_out:
        file_out.write(
            f"# {' '.join([word.capitalize() for word in machine_name.split('_')])}\n"
        )
        file_out.write("\n")
        if machine.__todo__:
            file_out.write(f"> todo: {machine.__todo__}\n")
            file_out.write("\n")
        file_out.write(f"![System Diagram]({machine_name}.svg)\n")
        file_out.write("\n")
        file_out.write(f"::: {machine.__module__}.{machine_class}\n")
        file_out.write("    options:\n")
        file_out.write("        show_source : true\n")
