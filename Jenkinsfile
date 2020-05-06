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
            def run_py_dl = sh(
                script: 'cd config;. venv/bin/activate; python3.7 run.py download', returnStatus: true
            )
            if (run_py_dl == 0) { // upload raw to s3
                sh 'cd config; s3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put -r data/raw s3://kg-hub-public-data/raw'
            } else { // 'run.py download' failed - let's try to download last good copy of raw/ from s3 to data/
                sh 'cd config; rm -fr data/raw'
                sh 'cd config; s3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate get -r s3://kg-hub-public-data/raw data/'
            }
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
                sh 'cd config;. venv/bin/activate; pigz merged-kg.tar'
            }
        }
        stage('Convert to RDF') {
            steps {
                sh 'cd config;. venv/bin/activate; kgx transform --input-type tsv --output-type nt -o ./merged-kg.nt merged-kg.tar.gz'
                sh 'cd config;. venv/bin/activate; pigz merged-kg.nt'
            }
        }        
        stage('Publish') {
            steps {

                script {
                    if (env.BRANCH_NAME != 'jenkins') {
                        echo "Will not push if not on correct branch."
                    } else {
                        withCredentials([file(credentialsId: 's3cmd_kg_hub_push_configuration', variable: 'S3CMD_JSON')]) {
                            sh 'cd config; s3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put merged-kg.nt.gz s3://kg-hub-public-data/kg-covid-19.nt.gz'
                            sh 'cd config; s3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put merged-kg.tar.gz s3://kg-hub-public-data/kg-covid-19.tar.gz'
                            // Should now appear at:
                            // https://idg.berkeleybop.io/[artifact name]
                        }

                    }
                }
            }
        }
    }
}
