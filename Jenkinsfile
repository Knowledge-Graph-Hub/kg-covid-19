pipeline {
    agent any
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
                dir('./gitrepo') {
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
                dir('./gitrepo') {
                    script {
                        if (env.BRANCH_NAME != 'master') {
                            echo "Will not push if not on correct branch."
                        } else {
                            def run_py_dl = sh(
                                script: '. venv/bin/activate && python3.7 run.py download', returnStatus: true
                            )
                            withCredentials([file(credentialsId: 's3cmd_kg_hub_push_configuration', variable: 'S3CMD_JSON')]) {
                                def s3cmd_with_args = 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate'
                                if (run_py_dl == 0) { // upload raw to s3
                                    sh '${s3cmd_with_args} put -r data/raw s3://kg-hub-public-data/'
                                } else { // 'run.py download' failed - let's try to download last good copy of raw/ from s3 to data/
                                    sh 'rm -fr data/raw || true;'
                                    sh 'mkdir -p data/raw || true'
                                    sh '${s3cmd_with_args} get -r s3://kg-hub-public-data/raw/ data/raw/'
                                }
                            }
                        }
                    }
                }
            }
        }

        stage('Transform') {
            steps {
                dir('./gitrepo') {
                    sh '. venv/bin/activate && python3.7 run.py transform'
                }
            }
        }

        stage('Load') {
            steps {
                dir('./gitrepo') {
                    sh '. venv/bin/activate && python3.7 run.py load'
                    sh 'pigz merged-kg.tar'
                }
            }
        }

        stage('Convert to RDF') {
            steps {
                dir('./gitrepo') {
                    sh '. venv/bin/activate && kgx transform --input-type tsv --output-type nt -o ./merged-kg.nt merged-kg.tar.gz'
                    sh 'pigz merged-kg.nt'
                }
            }
        }

        stage('Publish') {
            steps {
                dir('./gitrepo') {
                    script {
                        if (env.BRANCH_NAME != 'master') {
                            echo "Will not push if not on correct branch."
                        } else {
                            withCredentials([file(credentialsId: 's3cmd_kg_hub_push_configuration', variable: 'S3CMD_JSON')]) {
                                def s3cmd_with_args = 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate'
                                sh '${s3cmd_with_args} put merged-kg.nt.gz s3://kg-hub-public-data/kg-covid-19.nt.gz'
                                sh '${s3cmd_with_args} put merged-kg.tar.gz s3://kg-hub-public-data/kg-covid-19.tar.gz'
                                // Should now appear at:
                                // https://kg-hub.berkeleybop.io/[artifact name]
                            }

                        }
                    }
                }
            }
        }
    }
}
