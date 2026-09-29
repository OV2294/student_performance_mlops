pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '15'))
        disableConcurrentBuilds()
    }

    // ---- Workflow scheduling ----
    triggers {
        // cron('H 2 * * *')            // nightly retrain at ~02:00
        pollSCM('H/5 * * * *')       // build within ~5 min of every push to GitHub
    }

    environment {
        PYTHONUTF8 = '1'
        PATH       = "${WORKSPACE}\\.venv\\Scripts;${env.PATH}"   // lets `dvc repro` find the venv's python
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
                .venv\\Scripts\\python -m pip install -r requirements.txt
                '''
            }
        }

        stage('DVC pipeline') {
            // generate_data -> preprocess -> train (MLflow) -> evaluate (quality gate) -> monitor (drift)
            steps {
                bat '''
                if not exist .dvc .venv\\Scripts\\dvc init
                .venv\\Scripts\\dvc cache dir --local C:\\dvc_cache
                .venv\\Scripts\\dvc repro --force
                '''
            }
        }

        stage('Show metrics') {
            steps {
                bat '''
                .venv\\Scripts\\dvc metrics show
                type reports\\drift_report.json
                '''
            }
        }

        stage('Tests') {
            steps {
                bat '''
                if not exist reports mkdir reports
                .venv\\Scripts\\python -m pytest tests --junitxml=reports\\junit.xml -q
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/*.json, models/model.joblib, dvc.lock', allowEmptyArchive: true
        }
        success { echo 'SUCCESS - data prepared, models trained and tracked in MLflow, quality gate and drift check done.' }
        failure { echo 'FAILED - check the stage logs above.' }
    }
}