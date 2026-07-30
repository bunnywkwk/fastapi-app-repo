pipeline {
    agent any

    environment {
        IMAGE_NAME       = 'fastapi-app'
        IMAGE_TAG        = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
        GITOPS_REPO_NAME = 'gitops-infra-repo'
    }

    stages {
        stage('Lint & Unit Test') {
            agent {
                docker { image 'python:3.11-slim' }
            }
            steps {
                echo "=== Running Linting and Unit Tests in Python 3.11 Container ==="
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    flake8 app/ tests/ --max-line-length=120
                    pytest -v
                '''
            }
        }

        stage('Build & Push Container Image') {
            when {
                branch pattern: '^(main|staging)$', comparator: 'REGEXP'
            }
            steps {
                echo "=== Building & Pushing Docker Image ==="
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker build -t ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG} .
                        docker push ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG}
                    '''
                }
            }
        }

        stage('Update GitOps Repo') {
            when {
                branch pattern: '^(main|staging)$', comparator: 'REGEXP'
            }
            steps {
                echo "=== Updating GitOps repo image tag via GitHub PAT ==="
                withCredentials([usernamePassword(credentialsId: 'github-pat-credentials', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                    sh '''
                        git config --global user.name "Jenkins CI Bot"
                        git config --global user.email "jenkins-ci@local.internal"
                        
                        rm -rf temp-gitops-repo
                        git clone https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${GITOPS_REPO_NAME}.git temp-gitops-repo
                        cd temp-gitops-repo

                        # Update deployment image tag dynamically
                        sed -i "s|image: .*/${IMAGE_NAME}:.*|image: ${GH_USER}/${IMAGE_NAME}:${IMAGE_TAG}|g" deployments/fastapi-deployment.yaml

                        git add deployments/fastapi-deployment.yaml
                        git commit -m "ci: update ${IMAGE_NAME} image tag to ${IMAGE_TAG} [skip ci]" || echo "No changes to commit"
                        git push https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${GITOPS_REPO_NAME}.git main
                        
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
    }
}
