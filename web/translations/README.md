1. Generate the message pot. From the root directory (not web), run the command:

   ```
   pybabel extract -F PyBabel.cfg -k _l -o web/translations/messages.pot .
   ```

2. Generate the translations:

   ```
   pybabel init -i web/translations/messages.pot -d web/translations -l es
   ```

   ```
   pybabel init -i web/translations/messages.pot -d web/translations -l fr
   ```

3. Edit the generated PO files, then:

   ```
   pybabel compile -d web/translations
   ```

4. Update, when needed (without deleting existing translations):

   ```
   pybabel extract -F web/translations/PyBabel.cfg -k _l -o web/translations/messages.pot .
   pybabel update -i web/translations/messages.pot -d web/translations
   ```
