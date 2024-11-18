# Command Line Construction

Automating interactions with command line tools is never trivial--especially if you need to parameterized the commands.  Properly quoting and escaping unknown values that are going to be provided as parameters to the command line tool is a beast.  Fortunately, Python provides a way of invoking a process as though it was a command line interaction that does all of the heavy lifting for us.  We just have to provide a list of strings that would have been the space-delimited elements of the command line had we entered it by hand.

However, there is one other requirement we want fulfilled, which is the ability to log the command that was submitted.  Having this information available when something doesn't behave as expected is invaluable.

But we cannot simply dump the raw strings to the log files.  The command line interactions sometimes require providing secret information that should not appear in a log file.  So what the framework provides is a way of constructing a list of strings that can be used for invoking a command line operation, but will not display secret information if just rendering the results as a string.

Let's consider one of the more complicated command line operations that needs to be performed--mounting a file share.

```bash
sudo -S mount -t cifs //some.file.share/client-name /backups/client-name -o username=account-name,password=account-key,serverino,nosharesock,actimeo=30,mfsymlinks,uid=1000,gid=1000
```

Embedded in the middle of the "-o" section is "password=account-key", and "account-key" is not something that should ever appear in a log file.

The implementation of mounting the file share looks like:

```python
    @classmethod
    def mount_storage(
        cls,
        *,
        unc: str,
        mount_path: str,
        account_name: str,
        account_key: SecretStr,
        user_id: str,
        actimeo: int = 30,
    ):
        """
        Mount a file share on a storage account.

        raises:
            Exception: If exit code is not zero.
        """
        command = SpaceDelimited(
            line=(
                "sudo",
                "-S",
                "mount",
                "-t",
                "cifs",
                unc,
                mount_path,
                "-o",
                CommaDelimited(
                    line=(
                        EqualDelimited(left="username", right=account_name),
                        EqualDelimited(left="password", right=account_key),
                        "serverino",
                        "nosharesock",
                        EqualDelimited(left="actimeo", right=str(actimeo)),
                        "mfsymlinks",
                        EqualDelimited(left="uid", right=user_id),
                        EqualDelimited(left="gid", right=user_id),
                    )
                ),
            )
        )

        cls.execute(command=command)
```

What the framework provides is a way to describe the command line in terms of how the items are delimited.  The reason for this convoluted way for describing the command line is it allows us to safely log what the command was.  In the parameters for the method, account_key has a type of SecretStr.  The behavior of a SecretStr is to render a masked output when used as a string.  In order to get the true value, you have to call the get_secret_value() method of the SecretStr.

The SpaceDelimited(..., CommaDelimited(..., EqualDelimited(left, right))) construct allows us to process the SecretStr values appropriately at the level in which they occur.  The logged output of the above construct looks like:

```bash
sudo -S mount -t cifs //p21d1290d50b001.file.core.windows.net/test-client-3 /backups/test-client-3 -o username=p21d1290d50b001,password=**********,serverino,nosharesock,actimeo=30,mfsymlinks,uid=1000,gid=1000
```

If you scroll to the right in the entry above, you will see that the password value is appropriately masked.

But when used to submit the operation to the OS, SpaceDelimited will unmask the SecretStr values.[^1]

[^1]:
    Strings that are intended to hold secret values should always be wrapped in something that provides default masking.  Doing so prevents accidental leakage of secrets (somebody decides to throw a print statement into the code).  It also lets people who inherit your code know what needs to be protected.

The usage of the full convolution of describing the command line is only necessary when the value is a SecretStr.  In the example above, only the usage of account_key _needed_ to be wrapped in EqualDelimited.  The rest could have been implemeted as templated strings: e.g., f"username={account_name}" (EqualDelimited was used for the sake of consistency).

Let's take a look at the definitions of the SpaceDelimited chain to see how everything fits together.

```python linenums="1"
# standard library imports
from typing import Sequence

# standard library imports
from pydantic import SecretStr

# local imports
from .comma_delimited import CommaDelimited
from .equal_delimited import EqualDelimited


class SpaceDelimited:
    """
    Represents a sequence of space delimited strings.  When used as a normal string, secret vlaues
    will be masked.
    """

    def __init__(
        self, *, line: Sequence[str | SecretStr | CommaDelimited | EqualDelimited]
    ):
        self._line = line

    def get_secret_value(self) -> list[str]:
        """
        Renders space delimited items as a list rather than a single string.  Secret values will be unmasked.
        """
        return [
            (
                item.get_secret_value()
                if isinstance(item, CommaDelimited)
                or isinstance(item, EqualDelimited)
                or isinstance(item, SecretStr)
                else item
            )
            for item in self._line
        ]

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return " ".join([str(item) for item in self._line])
```

Starting with the signature of the constructor:

```python linenums="18"
    def __init__(
        self, *, line: Sequence[str | SecretStr | CommaDelimited | EqualDelimited]
    ):
```

- self is the first paramter of every instance method in Python.  It provides the class context for the instance of the object.
- "\*" means that all of the parameters following the "\*" must be provided as named parameters.  Usage of named parameters rather than positional parameters facilitates inheriting someone else's code.
- line is the definition of the command line.
    - Sequence means the constructor is expecting either a list or a tuple of items.
    - The pipe delimited section means the list can contain any mix of strings (str), SecretStr, CommaDelimited, or EqualDelimited objects.  The technical term for this is "discriminated union", but in terms of reading the definition, traditionally in programming languages "|" means "or", so the usage of "|" in a type signature means "type or type or type...".  It's a way of letting the static type checker know the types the implementation can handle.

The two methods at the end are overriding built-in functionality for classes.

```python linenums="38"
    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return " ".join([str(item) for item in self._line])
```

\_\_repr\_\_ means "reproduce" and controls the representation of the object if it used in a print statement.  \_\_str\_\_ means string, and it controls the representation of object if it used as a string.  What we are doing here is making sure all of the contents of the line sequence are rendered as a string, which for SecretStr will come out masked.  CommaDelimited and EqualDelimited have similar overrides that unwind the nested aspects of a SpaceDelimited object into a single string.

The " ".join([...]) is the preferred idiom for concatenating strings in Python.  "join" is a method defined for string objects that says "place this string between every entry in the provided list of strings".  In this case, we wanted a space-delimited rendering of SpaceDelimited.  Python supports using the "+" operator for concatenation, but in general, usage of "join" is easier to maintain and has more predictable run-time performance.

```python
> hello_world = "Hello " + "world"
> print(hello_world)
Hello world
> hello_world = " ".join(["Hello", "world"])
> print(hello_world)
Hello world
> hello_world = "".join(["Hello", "world"])
Helloworld
```
Both approaches accomplish the same thing, but using "join" is much more flexible and maintainable (the last example shows how to join strings without a delimiter between them).

The guts of the functionality are found in the get_secret_value method.

```python linenums="23"
    def get_secret_value(self) -> list[str]:
        """
        Renders space delimited items as a list rather than a single string.  Secret values will be unmasked.
        """
        return [
            (
                item.get_secret_value()
                if isinstance(item, CommaDelimited)
                or isinstance(item, EqualDelimited)
                or isinstance(item, SecretStr)
                else item
            )
            for item in self._line
        ]
```

The name "get_secret_value" was selected because that is the name used to retrieve the unmasked value from a SecretStr.  Using that name allowed us to use the same method call for CommaDelimited, EqualDelimited, and SecretStr.  Per the constructor signature, the only other kind of object that could appear in a SpaceDelimited line is a string, which can be rendered as-is.

The construct of the return value is know as a list-comprehension, and reading it starts with the "for" statement at the bottom, which says "for each value in the sequence create an entry in a new list of items".  The "create an entry" is the part at the top of the construct.  The parenthesis are there for readability.  They aren't a necessary part of the syntax, but the conditional part of "create an entry" is more complicated than what you would typically see in a list-comprehension.

A more typical use case would be creating a list of only name values from a list of records you retrieved from a database.  An in-line conditional can appear on either side of the for statement. When on the left side of the for statement, you must provide an else clause to provide a value for the entry.  When on the right side of the for statement, you cannot provide an else clause, because it's serving as a filter to exclude some entries:

```python
> records = [{"name": "Bob", "id": 0, "phone_number": "xxx-xxxx"}, {"name": "Judy", "id": 1, "phone_number": "yyy-yyyy"}]
> names = [record["name"] for record in records]
> print(names)
["Bob", "Judy"]
> left_iffed = [record["name"] if record["id"] == 0 else "Who?" for record in records]
> print(left_iffed)
["Bob", "Who?"]
> right_iffed = [record["name"] for record in records if record["id"] == 0]
> print(right_iffed)
["Bob"]
```

Anyway, getting back to SpaceDelimited, if the item in the line sequence is an instance of a CommaDelimited, EqualDelimited, or SecretStr class, the entry will be created by calling the item's get_secret_value method.  For SecretStr, that's a straight-forward process--it's just going to return the unmasked value.  For CommaDelimited and EqualDelimited, things are a bit more complicated, but we'll get to those in a moment.  If it isn't one of those three types of objects, it has to be a string, so we just use the string as the entry in the list, which is what the else clause does.

Moving on to CommaDelimited:

```python linenums="1"
# standard library imports
from typing import Sequence

# third party imports
from pydantic import SecretStr

# local imports
from .equal_delimited import EqualDelimited


class CommaDelimited:
    """
    Represents a sequence of strings that are rendered as comma delimited.  When used as a normal string,
    the secret values will be masked.
    """

    def __init__(self, *, line: Sequence[str | SecretStr | EqualDelimited]):
        self._line = line

    def get_secret_value(self) -> str:
        """
        Performs the rendering including the unmasking of secret values.
        """
        return ",".join(
            [
                (
                    item.get_secret_value()
                    if isinstance(item, EqualDelimited) or isinstance(item, SecretStr)
                    else item
                )
                for item in self._line
            ]
        )

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return ",".join([str(item) for item in self._line])
```

The difference in the line signature is that CommaDelimited can only accept string, SecretStr, or EqualDelimited objects.

The \_\_str\_\_ is comma-delimited rather than space-delimited but otherwise works the same (SecretStr will be masked).

The get_secret_method returns a comma-delimited string instead of a list, because when it is called by SpaceDelimited's get_secret_value, we want it to be part of a non-nested list of strings.  Here, the list-comprehension only has to conditionally react to EqualDelimited and SecretStr.  Any other objects in the CommaDelimited line will be strings.

And, finally, we have EqualDelimited:

```python linenums="1"
# third party imports
from pydantic import SecretStr


class EqualDelimited:
    """
    Represents a pair of strings that are delimited using an equals sign.  When used as a normal string,
    secret values will be masked.
    """

    def __init__(self, *, left: str, right: str | SecretStr):
        self._left = left
        self._right = right

    def get_secret_value(self) -> str:
        """
        Renders an equals delimited string with secret values unmasked.
        """
        return "=".join(
            (
                self._left,
                (
                    self._right.get_secret_value()
                    if isinstance(self._right, SecretStr)
                    else self._right
                ),
            )
        )

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return "=".join((self._left, str(self._right)))
```

In this case, "=" is an in-fix operator, so the signature only accepts a "to the left side of =", which can only be a string, and "to the right side of =", which can be either a string or a SecretStr.

\_\_str\_\_ is simply placing "=" between the parameter _left_ and the parameter _right_.  Again, rendering is masked for SecretStr values.

The get_secret_value method doesn't have a list-comprehension, because there are only two values.  Instead, it is placing "=" between _left_, which is a string, and _right_ which will be unmasked if it is a SecretStr or rendered as-is if it is a string.