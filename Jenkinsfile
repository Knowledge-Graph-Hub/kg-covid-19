pipeline {
    agent any
    triggers {
        // Every two days at 11 pm
        cron('0 23 */2 * *')
    }
    options {
        timestamps()
    }
    stages {
        // Very first: pause for a minute to give a chance to
        // cancel and clean the workspace before use.
        stage('Ready and clean') {
            steps {
                // Give us a minute to cancel if we want.
                sleep time: 1, unit: 'MINUTES'
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
                    sh '/usr/bin/python3.7 -m venv venv'
                    sh '. venv/bin/activate'
                    sh './venv/bin/pip install bmt'
                    sh './venv/bin/pip install -r requirements.txt'
                    sh './venv/bin/python setup.py install'
                }
            }
        }
        stage('Download') {
            steps {
                sh 'cd config;. venv/bin/activate; python3.7 run.py download'
            }
        }
        stage('Transform') {
            steps {
                sh 'cd config;. venv/bin/activate; python3.7 run.py transform'
            }
        }
        stage('Load') {
            steps {
                sh 'cd config;. venv/bin/activate; python3.7 run.py load'
            }
        }
        stage('Publish') {
            steps {

                script {
                    if (env.BRANCH_NAME != 'master') {
                        echo "Will not push if not on correct branch."
                    } else {
                        // Get trivial product back in hand.
                        sh 'echo thing > dow.txt'

                        // Push out to your S3 bucket.  The given
                        // command is for small to medium files. If
                        // you need something appropriate for large
                        // files, let me know.
                        withCredentials([file(credentialsId: 's3cmd_idg_push_configuration', variable: 'S3CMD_JSON')]) {
                            sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put dow.txt s3://idg-public-data/dow.txt'
                            // Should now appear at:
                            // https://idg.berkeleybop.io/dow.txt
                            // http://idg.berkeleybop.io/dow.txt
                        }

                    }
                }
            }
        }
    }
}
