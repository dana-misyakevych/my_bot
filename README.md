# Tsinovyk

Tsinovyk is a telegram bot based on AIOGRAM, who monitors prices in different stores

## Installation

For use this bot you need to set dependencies from requirements.txt

```bash
pip install requirements
```
## Usage
To start bot you need to run main.py
```bash
├── bot
│   ├── database
│   ├── handlers
│   ├── keyboards
│   ├── middlewares
│   ├── misc
│   └── utils
│   ├──  main.py <- this one
└── locales
```

For usage in POLLING mode use this settings
```python

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

```
WEBHOOK in the works
```python
...
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## LINK

[ME](https://t.me/oleh_harasymiuk/)