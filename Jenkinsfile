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

    // Optional override (leave empty). Accepts:
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

              # Helper downloader (curl -> wget -> python3)
              dl() {
                local url="$1" out="$2"
                if command -v curl >/dev/null 2>&1; then curl -fSL "$url" -o "$out" && return 0; fi
                if command -v wget >/dev/null 2>&1; then wget -O "$out" "$url" && return 0; fi
                if command -v python3 >/dev/null 2>&1; then
                  python3 - "$url" "$out" << 'PY'
import sys, urllib.request
u,o=sys.argv[1],sys.argv[2]; urllib.request.urlretrieve(u,o)
PY
                  return 0
                fi
                echo "No downloader available (curl/wget/python3)"; return 1
              }

              # Resolve streaming jar
              HSJ="${HADOOP_STREAMING_JAR:-}"
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
                  RESOLVED_JAR="$HSJ"   # allow file:///
                  echo "Using provided non-GCS jar path: $RESOLVED_JAR"
                fi
              fi

              # 2) Try public GCS
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

              # 3) Fallback to cluster local (then stage a known-good jar)
              if [[ -z "$RESOLVED_JAR" ]]; then
                RESOLVED_JAR="file:///usr/lib/hadoop-mapreduce/hadoop-streaming.jar"
                echo "Fallback to cluster-local path: $RESOLVED_JAR"
              fi

              # 4) Stage known-good jar to your bucket and switch to it
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

              echo "export HADOOP_STREAMING_RESOLVED_JAR=\"$RESOLVED_JAR\"" > .resolved_jar.env
              echo "Preflight OK. Using streaming jar: $RESOLVED_JAR"
            '''
          }
        }
      }
    }

    stage('Stage code (mapper/reducer) & data to GCS') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh '''#!/usr/bin/env bash
              set -Eeuo pipefail
              if [[ -f "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
                gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
              fi
              gcloud config set project "${PROJECT_ID}"

              JOB_ROOT="gs://${BUCKET}/${JOB_NAME}/${BUILD_NUMBER}"
              CODE_PREFIX="${JOB_ROOT}/code"
              DATA_PREFIX="${JOB_ROOT}/data"

              # discover mapper / reducer within repo
              MAP="${MAP:-}"
              RED="${RED:-}"
              if [[ -z "$MAP" ]]; then
                if [[ -f mapper.py ]]; then MAP=mapper.py; else MAP="$(git ls-files | grep -E '^mapper\\.py$|/?mapper\\.py$' | head -n1)"; fi
              fi
              if [[ -z "$RED" ]]; then
                if [[ -f reducer.py ]]; then RED=reducer.py; else RED="$(git ls-files | grep -E '^reducer\\.py$|/?reducer\\.py$' | head -n1)"; fi
              fi
              [[ -n "$MAP" && -n "$RED" ]] || { echo "mapper.py/reducer.py not found in repo"; exit 1; }
              echo "Mapper: $MAP"
              echo "Reducer: $RED"

              # clean and upload ONLY mapper & reducer under code/
              gsutil -m rm -r "${CODE_PREFIX}" >/dev/null 2>&1 || true
              gsutil -m cp "$MAP" "${CODE_PREFIX}/"
              gsutil -m cp "$RED" "${CODE_PREFIX}/"

              # pick data files from repo (flat) – .txt/.csv/.log by default
              gsutil -m rm -r "${DATA_PREFIX}" >/dev/null 2>&1 || true
              mkdir -p /tmp/upload_data

              found=0
              while IFS= read -r f; do
                cp "$f" "/tmp/upload_data/$(basename "$f")"
                found=1
              done < <(git ls-files | grep -Ei '\\.(txt|csv|log)$' || true)

              # if no data files in repo, create a tiny sample
              if [[ "$found" -eq 0 ]]; then
                echo "No data files found (*.txt, *.csv, *.log). Creating sample..."
                cat > /tmp/upload_data/sample.txt <<EOF
alpha
beta
gamma
alpha
beta
alpha
EOF
              fi

              gsutil -m cp /tmp/upload_data/* "${DATA_PREFIX}/"

              # persist paths for submit stage
              {
                echo "export CODE_PREFIX='${CODE_PREFIX}'"
                echo "export DATA_PREFIX='${DATA_PREFIX}'"
                echo "export MAP_BASENAME='$(basename "$MAP")'"
                echo "export RED_BASENAME='$(basename "$RED")'"
              } >> .resolved_jar.env

              echo "Staged code -> ${CODE_PREFIX}"
              echo "Staged data -> ${DATA_PREFIX}"
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

              # load resolved vars
              source .resolved_jar.env
              echo "Streaming JAR: ${HADOOP_STREAMING_RESOLVED_JAR}"
              echo "CODE_PREFIX  : ${CODE_PREFIX}"
              echo "DATA_PREFIX  : ${DATA_PREFIX}"

              OUT="gs://${BUCKET}/results/${JOB_NAME}/${BUILD_NUMBER}"
              gsutil -m rm -r "${OUT}" >/dev/null 2>&1 || true

              # Use files from flat data prefix only (avoid directories)
              # Ship mapper/reducer via -files from code prefix
              gcloud dataproc jobs submit hadoop \
                --cluster="${CLUSTER_NAME}" \
                --region="${REGION}" \
                --jar="${HADOOP_STREAMING_RESOLVED_JAR}" \
                -- \
                -D mapreduce.job.maps=2 \
                -D mapreduce.job.reduces=1 \
                -files "${CODE_PREFIX}/${MAP_BASENAME},${CODE_PREFIX}/${RED_BASENAME}" \
                -mapper "python3 ${MAP_BASENAME}" \
                -reducer "python3 ${RED_BASENAME}" \
                -input  "${DATA_PREFIX}/*" \
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
