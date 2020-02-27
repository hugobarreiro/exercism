def transform(legacy_data):
    new_data = dict()
    for value, letters in legacy_data.items():
        for letter in letters:
            if not isinstance(letter, str):
                raise TypeError('Informed item {letter} is not a string.'.format(letter=letter))
            if len(letter) != 1 or not letter.isalpha():
                raise ValueError('Informed string {letter} is not a letter.'.format(letter=letter))
            new_data[str.lower(letter)] = value
    return new_data
