pipeline {
  agent any
  environment {
    PYTHON_VERSION = '3.11'
  }
  stages {
    stage('Auto Tag') {
      steps {
        sh '''
          python3 -m venv venv
          . venv/bin/activate
          pip install gitag
          git config --global user.name "ci-bot"
          git config --global user.email "ci@example.com"
          gitag --ci --debug --changelog
        '''
      }
    }
  }
}
