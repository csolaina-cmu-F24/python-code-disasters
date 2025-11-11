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

  options {
    skipDefaultCheckout(true)
  }

  environment {
    PROJECT_ID   = "cloud-infra-project-473819"
    REGION       = "us-central1"
    CLUSTER_NAME = "hdp-cluster-2"
    BUCKET       = "pcd-output-cloud-infra-project-473819"
    SONAR_SERVER = "sonarqube"
    GCP_SA_CRED  = "gcp-sa"

    // Optional override (leave blank to auto-resolve below):
    // Examples you may set later:
    //  - "gs://hadoop-lib/hadoop-streaming/hadoop-streaming.jar"
    //  - "gs://hadoop-lib/hadoop-streaming.jar"
    //  - "file:///usr/lib/hadoop-mapreduce/hadoop-streaming.jar"
    HADOOP_STREAMING_JAR = ""
  }

  // Webhook primary; polling as fallback
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

    stage('Preflight: GCP & Dataproc connectivity + Resolve streaming JAR') {
      steps {
        container('cloud-sdk') {
          withCredentials([file(credentialsId: env.GCP_SA_CRED, variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
            sh '''#!/usr/bin/env bash
              set -euo pipefail

              # --- auth / basic checks ---
              if [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project "${PROJECT_ID}"
              gcloud config set dataproc/region "${REGION}"

              echo "== gcloud auth list ==" && gcloud auth list
              echo "== Describe Dataproc cluster ==" && gcloud dataproc clusters describe "${CLUSTER_NAME}" --region "${REGION}" >/dev/null
              echo "== Probe GCS bucket ==" && gsutil ls "gs://${BUCKET}/" || true

              # --- resolve Hadoop Streaming JAR ---
              # Priority:
              #   1) User-provided env HADOOP_STREAMING_JAR (if set)
              #   2) Public GCS locations (two common paths)
              #   3) Local cluster path (file://) – used as a last resort (cannot preflight check remotely)
              #   4) Download from Maven Central to this workspace and upload to your bucket, then use that GCS path.

              set +e
              RESOLVED_JAR=""

              # 1) If env provided and is gs://, verify it exists
              if [[ -n "${HADOOP_STREAMING_JAR}" ]]; then
                if [[ "${HADOOP_STREAMING_JAR}" == gs://* ]]; then
                  if gsutil ls "${HADOOP_STREAMING_JAR}" >/dev/null 2>&1; then
                    RESOLVED_JAR="${HADOOP_STREAMING_JAR}"
                    echo "Using provided Hadoop Streaming jar: ${RESOLVED_JAR}"
                  else
                    echo "Provided HADOOP_STREAMING_JAR not found: ${HADOOP_STREAMING_JAR}"
                  fi
                else
                  # allow file:/// path (cannot verify remotely)
                  RESOLVED_JAR="${HADOOP_STREAMING_JAR}"
                  echo "Using provided Hadoop Streaming jar (non-GCS): ${RESOLVED_JAR}"
                fi
              fi

              # 2) Try public GCS paths (only if not resolved yet)
              if [[ -z "${RESOLVED_JAR}" ]]; then
                for CANDIDATE in \
                  "gs://hadoop-lib/hadoop-streaming/hadoop-streaming.jar" \
                  "gs://hadoop-lib/hadoop-streaming.jar"
                do
                  if gsutil ls "${CANDIDATE}" >/dev/null 2>&1; then
                    RESOLVED_JAR="${CANDIDATE}"
                    echo "Resolved Hadoop Streaming jar at public GCS: ${RESOLVED_JAR}"
                    break
                  fi
                done
              fi

              # 3) Try known local path on cluster image (no preflight check possible here)
              if [[ -z "${RESOLVED_JAR}" ]]; then
                RESOLVED_JAR="file:///usr/lib/hadoop-mapreduce/hadoop-streaming.jar"
                echo "Falling back to cluster-local streaming jar path: ${RESOLVED_JAR}"
                echo "Note: if the Dataproc image lacks this jar, we'll install a GCS jar in the next step."
              fi

              # 4) If we picked the cluster-local path, proactively stage a known-good jar to our bucket and switch to that
              if [[ "${RESOLVED_JAR}" == file://* ]]; then
                echo "Staging known-good streaming jar to your bucket as a safety net..."
                # Choose a Hadoop streaming version compatible with Hadoop 3.x
                HADOOP_STREAMING_VERSION="3.3.6"
                LOCAL_JAR="hadoop-streaming-${HADOOP_STREAMING_VERSION}.jar"
                JAR_URL="https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-streaming/${HADOOP_STREAMING_VERSION}/hadoop-streaming-${HADOOP_STREAMING_VERSION}.jar"
                TARGET_GS="gs://${BUCKET}/lib/${LOCAL_JAR}"

                # Download and upload only if not already present
                if ! gsutil ls "${TARGET_GS}" >/dev/null 2>&1; then
                  echo "Downloading ${JAR_URL} ..."
                  curl -fSL "${JAR_URL}" -o "${LOCAL_JAR}"
                  echo "Uploading to ${TARGET_GS} ..."
                  gsutil cp "${LOCAL_JAR}" "${TARGET_GS}"
                else
                  echo "Jar already present at ${TARGET_GS}."
                fi

                # Use the staged jar from your bucket
                RESOLVED_JAR="${TARGET_GS}"
                echo "Resolved Hadoop Streaming jar (staged): ${RESOLVED_JAR}"
              fi

              # Persist for later stages
              echo "HADOOP_STREAMING_RESOLVED_JAR=${RESOLVED_JAR}" > .resolved_jar.env
              set -e
              echo "Preflight OK. Using streaming jar: ${RESOLVED_JAR}"
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
              set -euo pipefail
              if [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project "${PROJECT_ID}"

              INPUT_PATH="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"

              # Clean target prefix quietly if it exists
              gsutil -m rm -r "${INPUT_PATH}" >/dev/null 2>&1 || true

              # Upload only tracked *.py, preserve relative paths
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
              set -euo pipefail
              if [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
                gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
              fi
              gcloud config set project "${PROJECT_ID}"
              gcloud config set dataproc/region "${REGION}"

              # Load the resolved jar path from preflight
              source .resolved_jar.env
              echo "Submitting with streaming JAR: ${HADOOP_STREAMING_RESOLVED_JAR}"

              INPUT_PREFIX="gs://${BUCKET}/inputs/${JOB_NAME}/${BUILD_NUMBER}"
              OUT="gs://${BUCKET}/results/${JOB_NAME}/${BUILD_NUMBER}"

              # Discover mapper/reducer in repo (prefer root)
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

              MAP_GS="${INPUT_PREFIX}/${MAP}"
              RED_GS="${INPUT_PREFIX}/${RED}"

              # Clean output prefix quietly if present
              gsutil -m rm -r "${OUT}" >/dev/null 2>&1 || true

              # Submit Hadoop Streaming job
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

              # Print results
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
