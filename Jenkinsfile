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
    GCP_SA_CRED  = "gcp-sa"

    // Optional override (leave empty) — if you know a working path, set it to one of:
    //  - gs://hadoop-lib/hadoop-streaming/hadoop-streaming.jar
    //  - gs://<your-bucket>/lib/hadoop-streaming-3.3.6.jar
    //  - file:///usr/lib/hadoop-mapreduce/hadoop-streaming.jar
    HADOOP_STREAMING_JAR = ""
  }

  triggers { pollSCM('H/10 * * * *') }

  stages {
    stage('Checkout') {
      steps {
        container('cloud-sdk') {
          sh '''#!/usr/bin/env bash
            set -e
            git config --global --add safe.directory '*'
          '''
          checkout scm
          sh '''#!/usr/bin/env bash
            set -e
            git rev-parse --short HEAD
          '''
        }
      }
    }

    stage('SonarQube - Analyze') {
      steps {
        container('sonar') {
          withSonarQubeEnv("${env.SONAR_SERVER}") {
            sh '''#!/usr/bin/env bash
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
        timeout(time: 20, unit: 'MINUTES') {
          script {
            def qg = waitForQualityGate(abortPipeline: false)
            echo "Quality Gate: ${qg?.status ?: 'UNKNOWN'}"
            if (!qg || (qg.status != 'OK' && qg.status != 'SUCCESS')) {
              error "Quality Gate failed or not OK (status=${qg?.status})."
            }
          }
        }
      }
    }

    stage('Preflight: GCP & resolve Hadoop Streaming jar') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh '''#!/usr/bin/env bash
              set -Eeuo pipefail

              # auth / config
              if [[ -f "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
                gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
              fi
              gcloud config set project "${PROJECT_ID}"
              gcloud config set dataproc/region "${REGION}"

              echo "== gcloud auth list ==" && gcloud auth list
              echo "== Describe Dataproc cluster ==" && gcloud dataproc clusters describe "${CLUSTER_NAME}" --region "${REGION}" >/dev/null
              echo "== Probe GCS bucket ==" && gsutil ls "gs://${BUCKET}/" || true

              # Helper: robust downloader (curl -> wget -> python)
              dl() {
                local url="$1" out="$2"
                if command -v curl >/dev/null 2>&1; then
                  curl -fSL "$url" -o "$out" && return 0
                fi
                if command -v wget >/dev/null 2>&1; then
                  wget -O "$out" "$url" && return 0
                fi
                if command -v python3 >/dev/null 2>&1; then
                  python3 - "$url" "$out" << 'PY'
import sys, urllib.request
u,o=sys.argv[1],sys.argv[2]
urllib.request.urlretrieve(u,o)
PY
                  return 0
                fi
                echo "No downloader available (curl/wget/python3)"; return 1
              }

              # Resolve streaming jar
              HSJ="${HADOOP_STREAMING_JAR:-}"   # safe default avoids 'unbound variable'
              RESOLVED_JAR=""

              # 1) Use provided env if valid
              if [[ -n "$HSJ" ]]; then
                if [[ "$HSJ" == gs://* ]]; then
                  if gsutil ls "$HSJ" >/dev/null 2>&1; then
                    RESOLVED_JAR="$HSJ"
                    echo "Using provided Hadoop streaming jar: $RESOLVED_JAR"
                  else
                    echo "Provided HADOOP_STREAMING_JAR not found: $HSJ"
                  fi
                else
                  # allow file:/// (cannot preflight)
                  RESOLVED_JAR="$HSJ"
                  echo "Using provided non-GCS jar path: $RESOLVED_JAR"
                fi
              fi

              # 2) Try public GCS locations
              if [[ -z "$RESOLVED_JAR" ]]; then
                for C in \
                  "gs://hadoop-lib/hadoop-streaming/hadoop-streaming.jar" \
                  "gs://hadoop-lib/hadoop-streaming.jar"
                do
                  if gsutil ls "$C" >/dev/null 2>&1; then
                    RESOLVED_JAR="$C"
                    echo "Resolved jar via public GCS: $RESOLVED_JAR"
                    break
                  fi
                done
              fi

              # 3) Fallback to cluster local path (will still stage a known-good jar next)
              if [[ -z "$RESOLVED_JAR" ]]; then
                RESOLVED_JAR="file:///usr/lib/hadoop-mapreduce/hadoop-streaming.jar"
                echo "Fallback to cluster-local path: $RESOLVED_JAR"
              fi

              # 4) Stage known-good jar to your bucket and switch to it
              #    (ensures success even if cluster-local path doesn't exist)
              if [[ "$RESOLVED_JAR" == file://* ]]; then
                HVER="3.3.6"
                LOCAL="hadoop-streaming-${HVER}.jar"
                URL="https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-streaming/${HVER}/hadoop-streaming-${HVER}.jar"
                TARGET="gs://${BUCKET}/lib/${LOCAL}"

                if ! gsutil ls "$TARGET" >/dev/null 2>&1; then
                  echo "Downloading $URL ..."
                  dl "$URL" "$LOCAL"
                  echo "Uploading to $TARGET ..."
                  gsutil cp "$LOCAL" "$TARGET"
                else
                  echo "Jar already present at $TARGET"
                fi
                RESOLVED_JAR="$TARGET"
                echo "Resolved jar (staged): $RESOLVED_JAR"
              fi

              # Persist for next stage
              echo "export HADOOP_STREAMING_RESOLVED_JAR=\"$RESOLVED_JAR\"" > .resolved_jar.env
              echo "Preflight OK. Using streaming jar: $RESOLVED_JAR"
            '''
          }
        }
      }
    }

    stage('Prep inputs (upload .py to GCS)') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh '''#!/usr/bin/env bash
              set -Eeuo pipefail
              if [[ -f "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
                gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
              fi
              gcloud config set project "${PROJECT_ID}"

              INPUT_PATH="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"

              gsutil -m rm -r "${INPUT_PATH}" >/dev/null 2>&1 || true

              mkdir -p /tmp/upload_py
              while IFS= read -r f; do
                mkdir -p "/tmp/upload_py/$(dirname "$f")"
                cp "$f" "/tmp/upload_py/$f"
              done < <(git ls-files '*.py')

              (cd /tmp/upload_py && gsutil -m cp -r . "${INPUT_PATH}/")
              echo "Uploaded inputs to ${INPUT_PATH}"
            '''
          }
        }
      }
    }

    stage('Dataproc Hadoop Streaming') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh '''#!/usr/bin/env bash
              set -Eeuo pipefail
              if [[ -f "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
                gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
              fi
              gcloud config set project "${PROJECT_ID}"
              gcloud config set dataproc/region "${REGION}"

              # load resolved jar
              source .resolved_jar.env
              echo "Submitting with streaming JAR: ${HADOOP_STREAMING_RESOLVED_JAR}"

              INPUT_PREFIX="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"
              OUT="gs://${BUCKET}/results/${JOB_NAME}/${BUILD_NUMBER}"

              # discover mapper / reducer
              MAP="${MAP:-}"
              RED="${RED:-}"
              if [[ -z "$MAP" ]]; then
                if [[ -f mapper.py ]]; then MAP=mapper.py; else MAP="$(git ls-files | grep -E '/?mapper\\.py$' | head -n1)"; fi
              fi
              if [[ -z "$RED" ]]; then
                if [[ -f reducer.py ]]; then RED=reducer.py; else RED="$(git ls-files | grep -E '/?reducer\\.py$' | head -n1)"; fi
              fi
              [[ -n "$MAP" && -n "$RED" ]] || { echo "mapper.py/reducer.py not found"; exit 1; }

              echo "Using mapper: $MAP"
              echo "Using reducer: $RED"

              MAP_GS="${INPUT_PREFIX}/${MAP}"
              RED_GS="${INPUT_PREFIX}/${RED}"

              gsutil -m rm -r "${OUT}" >/dev/null 2>&1 || true

              gcloud dataproc jobs submit hadoop \
                --cluster="${CLUSTER_NAME}" \
                --region="${REGION}" \
                --jar="${HADOOP_STREAMING_RESOLVED_JAR}" \
                -- \
                -D mapreduce.job.maps=4 \
                -D mapreduce.job.reduces=2 \
                -files "${MAP_GS},${RED_GS}" \
                -mapper "python3 $(basename "${MAP}")" \
                -reducer "python3 $(basename "${RED}")" \
                -input "${INPUT_PREFIX}" \
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
    always {
      echo "Build #${env.BUILD_NUMBER} finished with status: ${currentBuild.currentResult}"
    }
  }
}
