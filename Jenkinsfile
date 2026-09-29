// Windows Jenkins pipeline: every step uses `bat` (cmd.exe) — no sh/Linux.
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 40, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '15'))
        disableConcurrentBuilds()
    }

    // ---- Workflow scheduling ----
    triggers {
        cron('H 2 * * *')            // nightly retrain at ~02:00 (scheduled workflow)
        pollSCM('H/5 * * * *')       // and on every new commit pushed to GitHub (CI)
    }

    environment {
        PYTHONUTF8    = '1'
        IMAGE_NAME    = 'student-performance-mlops'
        PATH          = "${WORKSPACE}\\.venv\\Scripts;${env.PATH}"   // so `dvc repro` finds the .venv's python
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Setup Python env') {
            steps {
                bat '''
                if not exist .venv python -m venv .venv
                .venv\\Scripts\\python -m pip install --upgrade pip
                .venv\\Scripts\\python -m pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Unit tests') {
            steps {
                bat 'if not exist reports mkdir reports'
                bat '.venv\\Scripts\\python -m pytest tests --junitxml=reports\\junit.xml -q'
            }
        }

        stage('Data + Train pipeline (DVC)') {
            steps {
                bat '''
                if not exist .dvc .venv\\Scripts\\dvc init
                .venv\\Scripts\\dvc cache dir --local C:\\dvc_cache
                .venv\\Scripts\\dvc repro --force
                '''
            }
        }

        stage('Quality gate & tests (with model)') {
            steps {
                bat '.venv\\Scripts\\python -m pytest tests --junitxml=reports\\junit.xml -q'
            }
        }

        stage('Drift monitoring') {
            steps { bat '.venv\\Scripts\\python -m src.monitor' }
        }

        stage('Docker build') {
            steps {
                bat '''
                docker build -t %IMAGE_NAME%:%BUILD_NUMBER% -t %IMAGE_NAME%:latest .
                '''
            }
        }

        stage('Deploy (docker compose)') {
            steps {
                bat '''
                docker compose down
                docker compose up -d
                '''
            }
        }

        stage('Smoke test') {
            steps { bat '.venv\\Scripts\\python scripts\\smoke_test.py http://localhost:8000' }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/*.json, models/model.joblib', allowEmptyArchive: true
        }
        success { echo 'Pipeline SUCCESS - model retrained, containerised and deployed.' }
        failure { echo 'Pipeline FAILED - check the stage logs above.' }
    }
}
