pipeline {
    agent any
    triggers {
	// Every two days at 11 pm
	cron('0 23 */2 * *')
    }
    options{
	timestamps()
    }
    stages {
	// Very first: pause for a minute to give a chance to
	// cancel and clean the workspace before use.
	stage('Ready and clean') {
	    steps {
		// Give us a minute to cancel if we want.
		// sleep time: 1, unit: 'MINUTES'
		cleanWs()
	    }
	}
	stage('Initialize') {
	    steps {
		// Start preparing environment.
		parallel(
		    "Report": {
			sh 'env > env.txt'
			sh 'echo $BRANCH_NAME > branch.txt'
			sh 'echo "$BRANCH_NAME"'
			sh 'cat env.txt'
			sh 'cat branch.txt'
			sh 'echo $START_DAY > dow.txt'
			sh 'echo "$START_DAY"'
		    })
	    }
	}

        stage('Build kg_covid_19') {
            steps {
                dir('./config') {
                    git(
                        url: 'https://github.com/Knowledge-Graph-Hub/kg-covid-19',
                        branch: 'master'
                    )
                    sh '''
		        cd kg_covid_19
		        virtualenv -p python3 venv --distribute
		        . venv/bin/activate
		        # ./venv/bin/pip install bmt
		        ./venv/bin/pip install -r requirements.txt
		        ./venv/bin/python setup.py install
		    '''
                }
            }
        }
        stage('Download') {
            steps {
                  echo "./venv/bin/python run.py download"
            }
        }
        stage('Transform') {
            steps {
                echo "./venv/bin/python run.py transform"
            }
        }
        stage('Load') {
            steps {
                echo "./venv/bin/python run.py load"
            }
        }
        stage('Push to s3 bucket') {
            steps {
                echo "???? # Need some details for this item"
            }
	}
    }
}
