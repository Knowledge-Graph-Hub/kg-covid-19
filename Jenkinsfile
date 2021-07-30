pipeline {
    agent {
        docker {
            image 'justaddcoffee/ubuntu20-python-3-8-5-dev:4'
        }
    }
    triggers{
        cron('H H 1 1-12 *')
    }
    environment {
        BUILDSTARTDATE = sh(script: "echo `date +%Y%m%d`", returnStdout: true).trim()
        S3PROJECTDIR = 'kg-covid-19' // no trailing slash

        // Distribution ID for the AWS CloudFront for this bucket
        // used solely for invalidations
        AWS_CLOUDFRONT_DISTRIBUTION_ID = 'EUVSWXZQBXCFP'
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
                sleep time: 30, unit: 'SECONDS'
            }
        }

        stage('Initialize') {
            steps {
                // print some info
                dir('./gitrepo') {
                    sh 'env > env.txt'
                    sh 'echo $BRANCH_NAME > branch.txt'
                    sh 'echo "$BRANCH_NAME"'
                    sh 'cat env.txt'
                    sh 'cat branch.txt'
                    sh "echo $BUILDSTARTDATE > dow.txt"
                    sh "echo $BUILDSTARTDATE"
                    // sh "python3.8 --version"
                    sh "id"
                    sh "whoami" // this should be jenkinsuser
                    // if the above fails, then the docker host didn't start the docker
                    // container as a user that this image knows about. This will
                    // likely cause lots of problems (like trying to write to $HOME
                    // directory that doesn't exist, etc), so we should fail here and
                    // have the user fix this
                }
            }
        }

        stage('Deploy blazegraph') {
            when { anyOf { branch 'check_ansible_run_jenkins' } }
            steps {
                sh 'echo FIX BRANCH CHECK ABOVE!!!'

                git([branch: 'master',
                         credentialsId: 'justaddcoffee_github_api_token_username_pw',
                         url: 'https://github.com/geneontology/operations.git'])

                dir('./ansible') {

                    withCredentials([file(credentialsId: 'ansible-bbop-local-slave', variable: 'DEPLOY_LOCAL_IDENTITY')]) {
                        echo 'Push master out to public Blazegraph'
                        sh 'while true; do; echo "sleeping...";sleep 2; done'
                        sh 'ansible-playbook update-kg-hub-endpoint.yaml --inventory=hosts.local-rdf-endpoint --private-key="$DEPLOY_LOCAL_IDENTITY" -e target_user=bbop --extra-vars="endpoint=internal"'
                    }

                }
            }
        }
    }

    post {
        always {
            echo 'Nothing to do (in always)'
        }
        success {
            echo 'I succeeded!'
        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo 'I failed :('
        }
        changed {
            echo 'Things were different before...'
        }
    }

}
