
 # 1 - Generate the message pot.
 from root dir (not web), run the command
 
`pybabel extract -F PyBabel.cfg -k _l -o web/translations/messages.pot .`

# 2 - generate the translations

`pybabel init -i web/translations/messages.pot -d web/translations -l es `

`pybabel init -i web/translations/messages.pot -d web/translations -l fr `



# 3 - edit the generated PO files, then

```
pybabel compile -d web/translations

```

# 4 update, when needed (without deleting existing translations)
`pybabel extract -F web/translations/PyBabel.cfg -k _l -o web/translations/messages.pot .`
`pybabel update -i web/translations/messages.pot -d web/translations`

