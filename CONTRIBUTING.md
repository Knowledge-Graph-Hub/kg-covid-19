# How to contribute code to KG-COVID-19

### Write a PR to ingest data from a new source

* read the documentation below about the GitHub Workflow

* find a source you'd like to ingest 
[here](https://github.com/Knowledge-Graph-Hub/kg-covid-19/issues?q=is%3Aopen+is%3Aissue+label%3A%22new+data+source%22)
(or make a new issue with the data source)

* following the guidelines [here](https://github.com/Knowledge-Graph-Hub/kg-covid-19/wiki/KG-COVID-19)
 to write a PR for the new ingest

### Basic principles of the [GitHub Workflow](http://guides.github.com/overviews/flow/)

##### Principle 1: Work from a personal fork 
* Prior to adopting the workflow, perform a *one-time setup* to create a personal Fork 
of the appropriate shared repo (e.g., `kg-covid-19`) and will subsequently perform 
their development and testing on a task-specific branch within their forked repo. This 
forked repo will be associated with that developer's GitHub account, and is distinct 
from the shared repo managed by the Monarch Initiative.

##### Principle 2: Commit to personal branches of that fork
* Changes will never be committed directly to the master branch on the shared repo. 
Rather, they will be composed as branches within the developer's forked repo, where the 
developer can iterate and refine their code prior to submitting it for review.

##### Principle 3: Propose changes via pull request of personal branches
*  Each set of changes will be developed as a task-specific *branch* in the developer's
forked repo, and then a [pull request](github.com/government/best-practices/compare) 
will be created to develop and propose changes to the shared repo. This mechanism 
provides a way for developers to discuss, revise and ultimately merge changes from the 
forked repo into the shared Monarch repo.

##### Principle 4: Delete or ignore stale branches, but don't recycle merged ones
*  Once a pull request has been merged, the task-specific branch is no longer needed 
and may be deleted or ignored. It is bad practice to reuse an existing branch once it 
has been merged. Instead, a subsequent branch and pull-request cycle should begin when 
a developer switches to a different coding task. 
*  You may create a pull request in order to get feedback, but if you wish to continue 
working on the branch, so state with "DO NOT MERGE YET".
