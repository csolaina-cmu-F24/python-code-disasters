// Jenkins on GKE: Kubernetes agent with two sidecar containers
//  - sonar-scanner CLI   (for analysis)
//  - google-cloud-cli    (for Dataproc submit)
//
// Prereqs (once per Jenkins):
// 1) Manage Jenkins → System → SonarQube servers: name = "sonarqube", URL=http://sonarqube:9000, token credential ID = SONAR_TOKEN
// 2) Manage Jenkins → Global Tool Config: SonarQube Scanner not needed (we use container image)
// 3) GitHub webhook → http(s)://<jenkins-external>/github-webhook/  (use Multibranch or GitHub branch source if preferred)
// 4) Dataproc auth: either Workload Identity on the Jenkins K8s SA OR a JSON key stored as Jenkins Secret Text/File with ID GCP_SA_KEY.
//    If using a key, Jenkinsfile will pick it up via credentialsId = 'GCP_SA_KEY'.

pipeline {
  agent {
    kubernetes {
      defaultContainer 'cloud-sdk'
      yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-dataproc-sonar
spec:
  serviceAccountName: jenkins
  restartPolicy: Never
  containers:
    - name: cloud-sdk
      image: gcr.io/google.com/cloudsdktool/google-cloud-cli:latest
      command: ['cat']
      tty: true
    - name: sonar
      image: sonarsource/sonar-scanner-cli:latest
      command: ['cat']
      tty: true
  """
    }
  }

  environment {
    PROJECT_ID   = "cloud-infra-project-473819"
    REGION       = "us-central1"
    CLUSTER_NAME = "hdp-cluster-2"
    // Bucket from your Terraform output:
    BUCKET       = "pcd-output-cloud-infra-project-473819"
    // Sonar server 'name' in Jenkins global config:
    SONAR_SERVER = "sonarqube"
  }

  triggers {
    // Poll fallback (use GitHub webhook primarily)
    pollSCM('H/5 * * * *')
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
            // sonar-project.properties must exist in repo
            sh """
              sonar-scanner \
                -Dsonar.projectKey=python-code-disasters-ci \
                -Dsonar.projectName=python-code-disasters-ci \
                -Dsonar.projectVersion=${env.BUILD_NUMBER} \
                -Dsonar.sources=. \
                -Dsonar.python.version=3
            """
          }
        }
      }
    }

    stage('Quality Gate') {
      steps {
        // Requires 'SonarQube Scanner for Jenkins' plugin; creates webhook automatically on first run
        timeout(time: 10, unit: 'MINUTES') {
          script {
            def qg = waitForQualityGate() // returns status and checks issues in SonarQube
            echo "Quality Gate: ${qg.status}"
            if (qg.status != 'OK') {
              error "Quality Gate failed or has blockers — skipping Hadoop job."
            }
          }
        }
      }
    }

    stage('Prep inputs for Hadoop (upload repo files to GCS)') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: 'GCP_SA_KEY', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh """
              set -e
              if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
                gcloud config set project ${PROJECT_ID}
              else
                # Workload Identity path: no key; ensure KSA -> GSA binding exists
                gcloud config set project ${PROJECT_ID}
                gcloud auth list
              fi

              # Create per-build input folder and copy source files
              INPUT_PATH=gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}
              gsutil -m rm -r ${INPUT_PATH} || true
              gsutil -m cp -r *.py ${INPUT_PATH}/ || true
              gsutil -m cp -r **/*.py ${INPUT_PATH}/ || true

              echo "Uploaded inputs to ${INPUT_PATH}"
            """
          }
        }
      }
    }

    stage('Dataproc Hadoop Streaming: Count lines per file') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: 'GCP_SA_KEY', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh """
              set -e
              if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project ${PROJECT_ID}
              gcloud config set dataproc/region ${REGION}

              INPUT=gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}
              OUT=gs://${BUCKET}/results/${JOB_NAME}/${BUILD_NUMBER}

              # Clean previous output
              gsutil -m rm -r ${OUT} || true

              # Submit Hadoop streaming job that counts lines per file.
              # Mapper emits "<filename>\\t1" per line, reducer sums.
              gcloud dataproc jobs submit hadoop \
                --cluster=${CLUSTER_NAME} \
                --region=${REGION} \
                -- \
                -D mapreduce.job.maps=4 \
                -D mapreduce.job.reduces=2 \
                -files mapper.py,reducer.py \
                -mapper "python3 mapper.py" \
                -reducer "python3 reducer.py" \
                -input ${INPUT} \
                -output ${OUT}

              echo "Job finished. Results at: ${OUT}"
              gsutil cat ${OUT}/part-*
            """
          }
        }
      }
    }
  }

  post {
    always {
      echo "Build #${env.BUILD_NUMBER} finished with status: ${currentBuild.currentResult}"
      archiveArtifacts artifacts: '**/target/*.jar', allowEmptyArchive: true
    }
  }
}
