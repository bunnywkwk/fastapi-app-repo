pipeline {
    agent any

    environment {
        DOCKER_HUB_USER  = 'your-dockerhub-username'
        IMAGE_NAME       = 'fastapi-app'
        IMAGE_TAG        = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
        GITOPS_REPO_URL  = 'git@github.com:your-user/gitops-infra-repo.git'
    }

    stages {
        stage('Lint & Unit Test') {
            steps {
                echo "=== Running Linting and Unit Tests on branch: ${env.BRANCH_NAME} ==="
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    flake8 app/ tests/ --max-line-length=120
                    pytest -v
                '''
            }
        }

        stage('Build Container Image') {
            when {
                branch pattern: "^(main|staging)$", comparator: "REGEXP"
            }
            steps {
                echo "=== Building Docker Image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ==="
                sh "docker build -t ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Push to Docker Hub') {
            when {
                branch pattern: "^(main|staging)$", comparator: "REGEXP"
            }
            steps {
                echo "=== Pushing Image to Docker Hub ==="
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        echo "$PASS" | docker login -u "$USER" --password-stdin
                        docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}
                    '''
                }
            }
        }

        stage('Update GitOps Repo') {
            when {
                branch pattern: "^(main|staging)$", comparator: "REGEXP"
            }
            steps {
                echo "=== Programmatically updating gitops-infra-repo image tag ==="
                withCredentials([sshUserPrivateKey(credentialsId: 'gitops-ssh-key', keyFileVariable: 'SSH_KEY')]) {
                    sh '''
                        export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o StrictHostKeyChecking=no"
                        rm -rf temp-gitops-repo
                        git clone ${GITOPS_REPO_URL} temp-gitops-repo
                        cd temp-gitops-repo

                        # Update deployment image tag using sed
                        sed -i "s|image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:.*|image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|g" deployments/fastapi-deployment.yaml

                        git config user.name "Jenkins CI Bot"
                        git config user.email "jenkins-ci@local.internal"
                        git add deployments/fastapi-deployment.yaml
                        git commit -m "ci: update ${IMAGE_NAME} image tag to ${IMAGE_TAG} [skip ci]" || echo "No changes to commit"
                        git push origin ${BRANCH_NAME}
                        cd ..
                        rm -rf temp-gitops-repo
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "=== Pipeline execution finished on branch ${env.BRANCH_NAME} ==="
            cleanWs()
        }
        success {
            echo "=== Pipeline completed successfully! ==="
        }
        failure {
            echo "=== Pipeline failed! Check logs above for details. ==="
        }
    }
}
