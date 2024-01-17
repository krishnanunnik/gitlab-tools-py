import json
import requests
import argparse
import csv
import os




class _GitlabVariables:
    def __init__(self, gitlab_url, gitlab_token, project_id):
        self.gitlab_url = gitlab_url
        self.gitlab_token = gitlab_token
        self.project_id = project_id
        self.endpoint = '{}/api/v4/projects/{}/variables'.format(self.gitlab_url, self.project_id)

    def get_variable(self, variable_name):
        headers = {'PRIVATE-TOKEN': self.gitlab_token}
        url = '{}/api/v4/projects/{}/variables'.format(self.gitlab_url, self.project_id)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for variable in response.json():
                if variable['key'] == variable_name:
                    return variable['value']
        return None

    def export_variables_as_csv(self, csv_file_path):
        headers = {'PRIVATE-TOKEN': self.gitlab_token}
        response = requests.get(self.endpoint, headers=headers)
        if response.status_code == 200:
            variables = response.json()
            field_names = list(variables[0].keys())
            writer = csv.DictWriter(open(csv_file_path, 'w', newline='', encoding='utf-8'), fieldnames=field_names)
            writer.writeheader()
            writer.writerows(variables)
            return True
        return False

    def create_new_variable(self, key, value, environment_scope="*", variable_type='env_var', protected=False,
                            masked=False, raw=False, description=None):

        headers = {'PRIVATE-TOKEN': self.gitlab_token}
        data = {
            "variable_type": variable_type or 'env_var',
            "key": key,
            "value": value,
            "protected": protected,
            "masked": masked,
            "raw": raw,
            "environment_scope": environment_scope,
            "description": description
        }
        response = requests.post(self.endpoint, headers=headers, json=data)
        if response.status_code == 201:
            return True
        return False

    def import_variables_from_csv(self, csv_file_path):
        with open(csv_file_path, 'r') as f:
            reader = csv.DictReader(f, fieldnames=['variable_type', 'key', 'value', 'protected', 'masked', 'raw',
                                                   'environment_scope', 'description'])
            next(reader)  # skip the header row
            for row in reader:
                self.create_new_variable(**row)
        return True


if __name__ == '__main__':
    argparse = argparse.ArgumentParser()
    argparse.add_argument('--gitlab-url', required=False, default=os.environ.get('GITLAB_URL', 'https://gitlab.com'))
    argparse.add_argument('--gitlab-token', required=False, default=os.environ.get('GITLAB_TOKEN'))
    argparse.add_argument('--project-id', required=False, default=os.environ.get('CI_PROJECT_ID'))
    argparse.add_argument('--file', required=False, default=os.environ.get('CI_ACTION_FILE'))
    argparse.add_argument('--action', required=False, default=os.environ.get('CI_ACTION', "export"),
                          choices=['export', 'import'])

    args = argparse.parse_args()
    gitlab_variables = _GitlabVariables(args.gitlab_url, args.gitlab_token, args.project_id)
    if args.action == 'export':
        gitlab_variables.export_variables_as_csv(args.file)
    elif args.action == 'import':
        gitlab_variables.import_variables_from_csv(args.file)
    else:
        raise Exception('Invalid action')
