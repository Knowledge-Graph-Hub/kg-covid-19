pipeline {
    agent any

    environment {
        BUILDSTARTDATE = sh(script: "echo `date +%Y%m%d`", returnStdout: true).trim()
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
                            sh "echo $BUILDSTARTDATE > dow.txt"
                            sh "echo $BUILDSTARTDATE"
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
                    sh './venv/bin/pip install wheel'
                    sh './venv/bin/pip install bmt'
                    sh './venv/bin/pip install -r requirements.txt'
                    sh './venv/bin/pip install .'
                }
            }
        }

        stage('Download') {
            steps {
                dir('./gitrepo') {
                    script {
                        def run_py_dl = sh(
                            script: '. venv/bin/activate && python3.7 run.py download', returnStatus: true
                        )
                        if (run_py_dl == 0) {
                            if (env.BRANCH_NAME != 'master') { // upload raw to s3 if we're on correct branch
                                echo "Will not push if not on correct branch."
                            } else {
                                withCredentials([file(credentialsId: 's3cmd_kg_hub_push_configuration', variable: 'S3CMD_JSON')]) {
                                    sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put -r data/raw s3://kg-hub-public-data/'
                                }
                            }
                        } else { // 'run.py download' failed - let's try to download last good copy of raw/ from s3 to data/
                            withCredentials([file(credentialsId: 's3cmd_kg_hub_push_configuration', variable: 'S3CMD_JSON')]) {
                                sh 'rm -fr data/raw || true;'
                                sh 'mkdir -p data/raw || true'
                                sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text get -r s3://kg-hub-public-data/raw/ data/raw/'
                            }
                        }
                    }
                }
            }
        }

        stage('Transform') {
            steps {
                dir('./gitrepo') {
                    sh 'env'
                    sh '. venv/bin/activate && env && python3.7 run.py transform'
                }
            }
        }

        stage('Merge') {
            steps {
                dir('./gitrepo') {
                    sh '. venv/bin/activate && python3.7 run.py merge'
                    sh 'env'
                    sh 'cp merged_graph_stats.yaml merged_graph_stats_$BUILDSTARTDATE.yaml'
                    sh 'tar -rvf data/merged/merged-kg.tar merged_graph_stats_$BUILDSTARTDATE.yaml'
                }
            }
        }

        stage('Make blazegraph journal'){
            steps {
                dir('./gitrepo/blazegraph') {
                        git(
                                url: 'https://github.com/balhoff/blazegraph-runner.git',
                                branch: 'master'
                        )
                        sh 'sbt stage'
                        sh 'pigz -d ../data/merged/merged-kg.nt.gz'
                        sh 'export JAVA_OPTS=-Xmx128G && ./target/universal/stage/bin/blazegraph-runner load --informat=ntriples --journal=../merged-kg.jnl --use-ontology-graph=true ../data/merged/merged-kg.nt'
                        sh 'pigz ../merged-kg.jnl'
                        sh 'pigz ../data/merged/merged-kg.nt'
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
                                sh 'rm -fr data/transformed/.gitkeep'
                                sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put -r data/transformed s3://kg-hub-public-data/'
                                sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put data/merged/merged-kg.nt.gz s3://kg-hub-public-data/kg-covid-19.nt.gz'
                                sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put data/merged/merged-kg.tar.gz s3://kg-hub-public-data/kg-covid-19.tar.gz'
                                sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put merged-kg.jnl.gz s3://kg-hub-public-data/kg-covid-19.jnl.gz'
                                sh 's3cmd -c $S3CMD_JSON --acl-public --mime-type=plain/text --cf-invalidate put *_stats.yaml s3://kg-hub-public-data/'
                                // Should now appear at:
                                // https://kg-hub.berkeleybop.io/[artifact name]
                            }

                        }
                    }
                }
            }
        }

        stage('Deploy blazegraph') {
            when { anyOf { branch 'master' } }
            steps {

                git([branch: 'master',
                     credentialsId: 'justaddcoffee_github_api_token_username_pw',
                     url: 'https://github.com/geneontology/operations.git'])

                dir('./ansible') {

                    withCredentials([file(credentialsId: 'ansible-bbop-local-slave', variable: 'DEPLOY_LOCAL_IDENTITY')]) {
                        echo 'Push master out to public Blazegraph'
                        retry(3){
                            sh 'ansible-playbook update-kg-hub-endpoint.yaml --inventory=hosts.local-rdf-endpoint --private-key="$DEPLOY_LOCAL_IDENTITY" -e target_user=bbop --extra-vars="endpoint=internal"'
                        }
                    }
                }

            }
        }

    }
}
