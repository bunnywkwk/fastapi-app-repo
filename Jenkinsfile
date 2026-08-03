pipeline {
    agent any

    environment {
        IMAGE_NAME       = 'fastapi-app'
        GIT_SHORT_SHA    = "${sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()}"
        IMAGE_TAG        = "${env.TAG_NAME ?: env.BRANCH_NAME + '-' + GIT_SHORT_SHA}"
        GITOPS_REPO_NAME = 'gitops-infra-repo'
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

        stage('Build & Push Container Image') {
            when {
                anyOf {
                    branch 'staging'
                    branch 'main'
                    buildingTag()
                }
            }
            steps {
                echo "=== Building & Pushing Docker Image Tagged: ${IMAGE_TAG} ==="
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
                anyOf {
                    branch 'staging'
                    buildingTag()
                }
            }
            steps {
                echo "=== Updating GitOps repo image tag ==="
                withCredentials([usernamePassword(credentialsId: 'github-pat-credentials', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                    sh '''
                        git config --global user.name "Jenkins CI Bot"
                        git config --global user.email "jenkins-ci@local.internal"
                        
                        rm -rf temp-gitops-repo
                        git clone https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${GITOPS_REPO_NAME}.git temp-gitops-repo
                        cd temp-gitops-repo

                        # 1. Determine if this is a Tag (Prod) or a Branch (Staging)
                        if [ -n "${TAG_NAME}" ]; then
                            echo "Detected Git Tag: ${TAG_NAME}. Updating PRODUCTION branch."
                            TARGET_BRANCH="main"
                            IMAGE_TO_SET="${TAG_NAME}"
                        else
                            echo "Detected Branch: ${BRANCH_NAME}. Updating STAGING branch."
                            TARGET_BRANCH="staging"
                            IMAGE_TO_SET="${IMAGE_TAG}"
                        fi

                        # 2. Checkout the correct target branch from GitOps Repo
                        git checkout $TARGET_BRANCH

                        # 3. Update the deployment image tag dynamically
                        sed -i "s|image: .*/${IMAGE_NAME}:.*|image: ${GH_USER}/${IMAGE_NAME}:${IMAGE_TO_SET}|g" deployments/fastapi-deployment.yaml

                        # 4. Commit and push back to that specific branch
                        git add deployments/fastapi-deployment.yaml
                        git commit -m "ci: update ${IMAGE_NAME} image to ${IMAGE_TO_SET} [skip ci]" || echo "No changes to commit"
                        git push https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${GITOPS_REPO_NAME}.git $TARGET_BRANCH
                        
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
