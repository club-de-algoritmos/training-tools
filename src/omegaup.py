import os

import libomegaup.omegaup.api as api

_OMEGAUP_API_TOKEN_VAR_NAME = 'OMEGAUP_API_TOKEN'


def get_omegaup_client() -> api.Client:
    return api.Client(api_token=os.environ[_OMEGAUP_API_TOKEN_VAR_NAME])


def _generate_api_token():
    print('You are about to generate a new omegaUp API token, please input your credentials:')
    username = input('  Username: ')
    password = input('  Password: ')
    client = api.Client(username=username, password=password)
    user = api.User(client)
    tokens = user.listAPITokens().tokens

    if len(tokens) >= 5:
        confirm = input(f'You have too many tokens ({len(tokens)}), do you want to delete one? (y/N)')
        if confirm.lower() != 'y':
            print('Not doing anything')
            return
        token_to_delete = tokens[0].name
        print(f'Deleting token "{token_to_delete}"')
        user.revokeAPIToken(name=token_to_delete)

    token = user.createAPIToken(name='training-tools').token
    print('WARNING: Store your API token in a safe place as it can be used to impersonate you')
    print(f'Generated API token: {token}')
    print(f'Please expose your API token via the environment variable {_OMEGAUP_API_TOKEN_VAR_NAME}:')
    print(f'  export {_OMEGAUP_API_TOKEN_VAR_NAME}="{token}"')


if __name__ == '__main__':
    _generate_api_token()
