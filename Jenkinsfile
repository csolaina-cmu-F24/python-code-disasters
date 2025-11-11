pipeline {
  agent {
    kubernetes {
      cloud 'kubernetes'
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

  options { skipDefaultCheckout(true) }

  environment {
    PROJECT_ID   = "cloud-infra-project-473819"
    REGION       = "us-central1"
    CLUSTER_NAME = "hdp-cluster-2"
    BUCKET       = "pcd-output-cloud-infra-project-473819"
    SONAR_SERVER = "sonarqube"
    // Set your Jenkins file credential ID for the GCP SA key:
    GCP_SA_CRED  = "gcp-sa"
  }

  triggers { pollSCM('H/10 * * * *') }

  stages {
    stage('Checkout') {
      steps {
        container('cloud-sdk') {
          // Use bash to avoid dash quirks
          sh(script: '''
            git config --global --add safe.directory '*'
          ''', shell: '/bin/bash')
          checkout scm
          sh(script: 'git rev-parse --short HEAD', shell: '/bin/bash')
        }
      }
    }

    stage('SonarQube - Analyze') {
      steps {
        container('sonar') {
          withSonarQubeEnv("${env.SONAR_SERVER}") {
            sh(script: '''
              set -e
              export SONAR_TOKEN="$SONAR_AUTH_TOKEN"
              sonar-scanner \
                -Dsonar.projectKey=python-code-disasters-ci \
                -Dsonar.projectName=python-code-disasters-ci \
                -Dsonar.projectVersion=${BUILD_NUMBER} \
                -Dsonar.sources=. \
                -Dsonar.python.version=3
            ''', shell: '/bin/bash')
          }
        }
      }
    }

    stage('Quality Gate') {
      steps {
        timeout(time: 20, unit: 'MINUTES') {
          script {
            def qg = waitForQualityGate(abortPipeline: false)
            echo "Quality Gate initial status: ${qg?.status ?: 'UNKNOWN'}"
            if (qg == null || (qg.status != 'OK' && qg.status != 'SUCCESS')) {
              error "Quality Gate failed or not OK (status=${qg?.status})."
            }
          }
        }
      }
    }

    stage('Preflight: GCP & Dataproc connectivity') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh(script: '''
              set -euo pipefail
              if [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project "${PROJECT_ID}"
              gcloud config set dataproc/region "${REGION}"

              echo "== gcloud auth list =="
              gcloud auth list

              echo "== Describe Dataproc cluster =="
              gcloud dataproc clusters describe "${CLUSTER_NAME}" --region "${REGION}" >/dev/null

              echo "== Probe GCS bucket =="
              gsutil ls "gs://${BUCKET}/" || true

              echo "Preflight OK."
            ''', shell: '/bin/bash')
          }
        }
      }
    }

    stage('Prep inputs (upload .py to GCS)') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh(script: '''
              set -euo pipefail
              if [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project "${PROJECT_ID}"

              INPUT_PATH="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"
              gsutil -m rm -r "${INPUT_PATH}" || true

              # Collect only tracked *.py files and preserve paths
              mkdir -p /tmp/upload_py
              while IFS= read -r f; do
                mkdir -p "/tmp/upload_py/$(dirname "$f")"
                cp "$f" "/tmp/upload_py/$f"
              done < <(git ls-files '*.py')

              (cd /tmp/upload_py && gsutil -m cp -r . "${INPUT_PATH}/")
              echo "Uploaded inputs to ${INPUT_PATH}"
            ''', shell: '/bin/bash')
          }
        }
      }
    }

    stage('Dataproc Hadoop Streaming') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh(script: '''
              set -euo pipefail
              if [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project "${PROJECT_ID}"
              gcloud config set dataproc/region "${REGION}"

              INPUT="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"
              OUT="gs://${BUCKET}/results/${JOB_NAME}/${BUILD_NUMBER}"

              # Locate mapper/reducer anywhere in repo (prefers root if present)
              MAP=${MAP:-}
              RED=${RED:-}
              if [[ -z "$MAP" ]]; then
                if [[ -f mapper.py ]]; then MAP=mapper.py; else MAP="$(git ls-files | grep -E '/?mapper\\.py$' | head -n1)"; fi
              fi
              if [[ -z "$RED" ]]; then
                if [[ -f reducer.py ]]; then RED=reducer.py; else RED="$(git ls-files | grep -E '/?reducer\\.py$' | head -n1)"; fi
              fi
              [[ -n "$MAP" && -n "$RED" ]] || { echo "mapper.py/reducer.py not found"; exit 1; }

              echo "Using mapper: $MAP"
              echo "Using reducer: $RED"

              gsutil -m rm -r "${OUT}" || true

              gcloud dataproc jobs submit hadoop \
                --cluster="${CLUSTER_NAME}" \
                --region="${REGION}" \
                -- \
                -D mapreduce.job.maps=4 \
                -D mapreduce.job.reduces=2 \
                -files "$MAP,$RED" \
                -mapper "python3 $(basename "$MAP")" \
                -reducer "python3 $(basename "$RED")" \
                -input "${INPUT}" \
                -output "${OUT}"

              gsutil cat "${OUT}"/part-* | tee line_counts.txt
            ''', shell: '/bin/bash')
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
    always {
      echo "Build #${env.BUILD_NUMBER} finished with status: ${currentBuild.currentResult}"
    }
  }
}
