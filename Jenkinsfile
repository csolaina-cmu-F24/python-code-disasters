pipeline {
  agent {
    kubernetes {
      defaultContainer 'cloud-sdk'
      yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-dataproc-sonar
spec:
  serviceAccountName: jenkins
  restartPolicy: Never
  containers:
    - name: jnlp
      image: jenkins/inbound-agent:3192.v713e3b_039fb_e-1
      args: ['$(JENKINS_SECRET)', '$(JENKINS_NAME)']
    - name: cloud-sdk
      image: gcr.io/google.com/cloudsdktool/google-cloud-cli:latest
      command: ['cat']
      tty: true
    - name: sonar
      image: sonarsource/sonar-scanner-cli:latest
      command: ['cat']
      tty: true
'''
    }
  }

  environment {
    PROJECT_ID   = "cloud-infra-project-473819"
    REGION       = "us-central1"
    CLUSTER_NAME = "hdp-cluster-2"
    BUCKET       = "pcd-output-cloud-infra-project-473819"
    SONAR_SERVER = "sonarqube"
  }

  triggers {
    // keep as fallback; primary is GitHub webhook
    pollSCM('H/10 * * * *')
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'git rev-parse --short HEAD'
      }
    }

    stage('SonarQube - Analyze') {
      steps {
        container('sonar') {
          withSonarQubeEnv("${env.SONAR_SERVER}") {
            sh '''
              set -e
              export SONAR_TOKEN="$SONAR_AUTH_TOKEN"
              sonar-scanner \
                -Dsonar.projectKey=python-code-disasters-ci \
                -Dsonar.projectName=python-code-disasters-ci \
                -Dsonar.projectVersion=${BUILD_NUMBER} \
                -Dsonar.sources=. \
                -Dsonar.python.version=3
            '''
          }
        }
      }
    }

    stage('Quality Gate') {
      steps {
        timeout(time: 10, unit: 'MINUTES') {
          script {
            def qg = waitForQualityGate()
            echo "Quality Gate: ${qg.status}"
            if (qg.status != 'OK') {
              error "Quality Gate failed or has blockers — skipping Hadoop job."
            }
          }
        }
      }
    }

    stage('Prep inputs (upload .py to GCS)') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: 'GCP_SA_KEY', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh '''
              set -euo pipefail
              if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project ${PROJECT_ID}
              INPUT_PATH="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"
              gsutil -m rm -r "${INPUT_PATH}" || true
              mkdir -p /tmp/upload_py
              find . -type f -name '*.py' -print0 | xargs -0 -I{} cp --parents {} /tmp/upload_py/
              (cd /tmp/upload_py && gsutil -m cp -r . "${INPUT_PATH}/")
            '''
          }
        }
      }
    }

    stage('Dataproc Hadoop Streaming') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: 'GCP_SA_KEY', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh '''
              set -euo pipefail
              if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project ${PROJECT_ID}
              gcloud config set dataproc/region ${REGION}

              INPUT="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"
              OUT="gs://${BUCKET}/results/${JOB_NAME}/${BUILD_NUMBER}"

              test -f mapper.py && test -f reducer.py

              gsutil -m rm -r "${OUT}" || true

              gcloud dataproc jobs submit hadoop \
                --cluster="${CLUSTER_NAME}" \
                --region="${REGION}" \
                -- \
                -D mapreduce.job.maps=4 \
                -D mapreduce.job.reduces=2 \
                -files mapper.py,reducer.py \
                -mapper "python3 mapper.py" \
                -reducer "python3 reducer.py" \
                -input "${INPUT}" \
                -output "${OUT}"

              gsutil cat "${OUT}"/part-* | tee line_counts.txt
            '''
          }
        }
      }
    }
  }

  post {
    success {
      publishHTML(target: [
        reportName: 'Hadoop Results',
        reportDir: '.',
        reportFiles: 'line_counts.txt',
        keepAll: true,
        alwaysLinkToLastBuild: true,
        allowMissing: true
      ])
    }
  }
}
