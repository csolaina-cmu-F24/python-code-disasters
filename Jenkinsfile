pipeline {
  agent any

  environment {
    // TODO: Set these in Jenkins → Configure (or JCasC).
    // PROJECT_ID = 'my-gcp-project'
    // REGION     = 'us-central1'
    // CLUSTER    = 'hdp-cluster'
    // GCS_BUCKET = "gs://pcd-output-my-gcp-project"
    SONAR_SERVER = 'sonarqube-server' // TODO: must match Jenkins global config
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('SonarQube Analysis') {
      steps {
        withSonarQubeEnv("${env.SONAR_SERVER}") {
          script {
            // Use SonarScanner CLI in Docker (no tool install needed on agent)
            docker.image('sonarsource/sonar-scanner-cli:latest').inside {
              sh 'sonar-scanner'
            }
          }
        }
      }
    }

    stage('Quality Gate') {
      steps {
        timeout(time: 5, unit: 'MINUTES') {
          // Requires SonarQube → Jenkins webhook to be configured by infra
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Prepare Hadoop Input') {
      steps {
        sh '''
          set -euo pipefail
          test -n "${GCS_BUCKET:-}" || (echo "GCS_BUCKET env not set" && exit 1)

          rm -rf input && mkdir -p input
          # Copy all tracked files
          git ls-files | while read -r f; do
            if [ -f "$f" ]; then
              mkdir -p "input/$(dirname "$f")"
              cp "$f" "input/$f"
            fi
          done

          # Sync to GCS for Dataproc job input
          gsutil -m rsync -r input "${GCS_BUCKET}/input"
        '''
      }
    }

    stage('Run Hadoop Job (Dataproc Streaming)') {
      steps {
        sh '''
          set -euo pipefail
          for v in PROJECT_ID REGION CLUSTER GCS_BUCKET; do
            eval "val=\${$v:-}"
            [ -n "$val" ] || (echo "$v is not set" && exit 1)
          done

          # Upload streaming scripts
          gsutil cp hadoop/mapper.py  "${GCS_BUCKET}/mapper.py"
          gsutil cp hadoop/reducer.py "${GCS_BUCKET}/reducer.py"

          OUT="${GCS_BUCKET}/output-$(date +%s)"

          # Submit Hadoop Streaming job (counts lines per file)
          gcloud dataproc jobs submit hadoop \
            --project="${PROJECT_ID}" \
            --region="${REGION}" \
            --cluster="${CLUSTER}" \
            --class=org.apache.hadoop.streaming.HadoopStreaming \
            -- \
            -files "${GCS_BUCKET}/mapper.py,${GCS_BUCKET}/reducer.py" \
            -mapper "python3 mapper.py" \
            -reducer "python3 reducer.py" \
            -input  "${GCS_BUCKET}/input" \
            -output "${OUT}"

          echo "Job output path: ${OUT}"
        '''
      }
    }

    stage('Show Results') {
      steps {
        sh '''
          set -euo pipefail
          LAST=$(gsutil ls "${GCS_BUCKET}/" | grep 'output-' | sort | tail -n1)
          echo "Latest job output path: $LAST"
          gsutil cat "${LAST}"*/part-* || true
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'input/**', allowEmptyArchive: true
    }
  }
}
