# state_machine

Framework for safely implementing scripting hackiness in a production environment.

Having found your way here, my first suggestion would be to check out whether [Airflow](https://airflow.apache.org/) suits your needs better.  Long term, centralized management of Workflow Orchestration will be better than custom solutions.  Once it has been demonstrated that automation can be quickly and reliably generated, use cases proliferate.  It would behoove you to have something that facilitates keeping track of the automated tasks.

One common problem I have encountered in complicated systems is a tendancy to automate maintenance tasks using scripting languages, and the implementations are almost always very naive:

* No thought is put into exception handling--they assume the happy-path will always be followed.
* Credentials are not protected--clear text passwords frequently found in code, configs, and logs.
* Inefficient and difficult to parallelize.
* Usually undocumented--it's often quicker the throw it away and start over from scratch than reverse engineer what somebody else built.
* Lack of idempotence--failures often leave the system in an undesirable state.
* Take an exceedingly long time to create--cannot separate testing of the business logic from end-to-end testing ("quick and dirty" isn't quick--it's just dirty).
* Ad hoc or no failure reporting--a huge problem in code that is intended to run without anybody paying attention to what it's doing.

State machines provide a pattern for automating maintenance tasks that I have implemented frequently enough to justify creating a framework to simplify the process.  State machines have several advantages over happy-hacking my way through implementations:

* Easy to verify there is behavior defined for both the happy-path and all of the potential unhappy-paths.
* Easy to communicate what the automation is doing to stakeholders.
* Easy to identify insert points where modifications in the code need to be made.
* Easy to maintain the documentation--the diagrams are derived from the implementation.
* Easy to generalize--state machines are composable--just have one state machine invoke another.
* Easy to parallelize--see line above.

Additionally, the framework provides credential management functionality that makes it more convenient to use encrypted values than copy-and-paste hard-coded clear-text values.  There is also convenient protection against clear-text credentials leaking into the log files.

Implementations follow an End Point<-->Service<-->Repository layering pattern that allows the important parts of the code to be executed in unit tests during development.  Exercising business logic with unit tests profoundly reduces the amount of time to create a script--no need to create a special test environment and wait for the database to be backed up to just to find out whether script is going to even reach the step where the backup is encrypted.  Yes, integration testing is important, but it doesn't have to be performed following every little edit you make to a script.

Finally, the Results pattern has been built into the framework to provide consistent failure reporting and prevents the situation where a failure prevents the processing potential successes.