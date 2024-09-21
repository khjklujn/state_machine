# state_machine
Framework for safely implementing scripting hackiness in a production environment.

One common problem I have encountered in complicated systems is a tendancy to automate maintenance tasks using scripting languages, and the implementations are almost always very naive:

* No thought is put into exception handling--they assume the happy-path will always be followed.
* Credentials are not protected.
* Inefficient and difficult to parallelize.
* Difficult to document--it's often quicker the throw it away and start over from scratch than reverse engineer what somebody else built.
* Lack of idempotence--failures often leave the system in an undesirable state.
* Take an exceedingly long time to create--cannot separate testing of the business logic from end-to-end testing ("quick and dirty" isn't quick--it's just dirty).

