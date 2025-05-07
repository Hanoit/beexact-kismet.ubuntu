def hook(hook_api):
    # Loop through each item in datas and remove those ending with the specified file types
    hook_api.add_datas(
        (item[0], item[1])
        for item in hook_api.datas
        if not (item[0].endswith('.csv') or
                item[0].endswith('.db') or
                item[0].endswith('.md') or
                item[0].endswith('.json') or
                item[0].endswith('.env') or
                item[0].endswith('.gitignore'))
    )