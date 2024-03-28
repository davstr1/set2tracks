
 # 1 - Generate the message pot.
 from boilersaas/src/boilersaas/, run the command
 
`pybabel extract -F translations/PyBabel.cfg -k _l -o translations/messages.pot .`

# 2 - generate the translations

`pybabel init -i translations/messages.pot -d translations -l es `

`pybabel init -i translations/messages.pot -d translations -l fr `

...

# 3 - edit the generated PO files, then

pybabel compile -d translations


# 4 update, when needed (without deleting existing translations)
`pybabel extract -F translations/PyBabel.cfg -k _l -o translations/messages.pot .`
`pybabel update -i translations/messages.pot -d translations`

