
# TODO 

- UPDATE the manual import process here (readme)
- check and end the translation
- check how to overright translations from web/translations
- integrate fb login
- integrate https://www.paddle.com/
- integrate https://daisyui.com/
- put an app on it, and test
- admin user management dashboard
- user page

~~- move the migration folder away
- properly configure the ignore folders and files that user can edit
- maybe build an install process to copy some files if user hasn't already touched them. (routes, templates...)~~

# Who cares
Probably nobody at this point. I'm not promoting this thing thing either.
I'm writting this for myself, but i have some manners, so it would hurt me to serve the curious soul a blank README.

# About
Ok so i didn't find something for flask that ticked all my boxes. 
Something that lets you straight out of the box like a pip install and a config file,
then booom you have fully functioning user registration, payment integration, tailwindcss, pre templates for logo, landing page and dashboard, so you can **just care about building the damn MVP for your SAAS**. (which is more than enough of a job for a man).
And if you have several apps, update all this in a breeze.
I mean something free, intented at code savy guys, and with no AI cowbells and gimmicks.


# Warning : MVP, WIP, DYOR ... !

Yes, so far this is an MVP, so no tests, no rainbows or wonderfull CI/CD pipeline...
Also, not written by an expert python wizard, even if i have coding skills, not the best at this, and learning as i go.
Projet gives me a tiggling sense i should be ashamed of it, which is good for an MVP they say.
Just maybe don't use it to run a jet plane full of passengers. Or don't make me responsible after.

Anyway it "works on my machine", and my mum loves it so shut up and dance.



# Working on my machine so far

Python 3.11.5 (Naked, in a virtual environment)

- user registration
- user login
- user login with Google
- lost password
- invite mode (where you send invite links)
- translation (half assed but working)
- dashboard, landing page
- pre made templates for all or that. (don't expect content thaugh. For this you'll have to fight personally with Tailwind)

# Roadmap that's actually going to be done
Cause i need it for all my projects, and i will need all my project for being able to eat one day.
- all the main login providers (fb,x...)
- chargebee integration (and stripe, but for my own needs, that would be chargebee)
- a proper admin dashboard

# Roadmap that "would be great"
- tests tests tests and pipeline
- "boilersaas", perhaps the name kindof sucks.
- Not inspired right now, but tell me if you think about something.



# Install

## First Get the thing (yep..)

```
gh repo clone davstr1/flask-boilersaas
```
or just download it.

## 1 - Setup 

On terminal

```
./setup.sh
```

Or if you want to develop the boilerplate, contribute to the project :
```
./setup.sh dev
```
This will install ./boilerplate locally instead of from a remote pip. So you can edit it and see immediatly the results.

## 2 - Fill web/.env with your data

# Run

```
npx tailwindcss -i ./web/static/css/tailwind/input.css -o ./web/static/css/tailwind/output.css --watch
python web/run.py
```


## Or manual install

### 1 - Install python dependencies

```
pip install -r web/requirements.txt
```

or if you want to developp the boilersaas, ( and contribute to the project) : 

```
pip install -r web/requirements_dev.txt
```

Then don't pip install the boilersaas from Pypi,
but do an editable install instead :

```
pip install -e ./boilersaas
```

Now you can edit ./boilersaas and see immediate results.


### 2 - Edit environment variables

Copy example.env into a .env, and fill it with your data.


## Notes

- DEV : don't ditch the /boilerplate folder.
This has css tailwind is listening too, which are crucial to the whole shebang.

- PROD : All you really need in prod is the content of the "web" folder.



# Styling and Templates

Most templates are in the package (boilerplate)
Like login, registration, header etc..
But you can overwrite anything, just copying the corresponding templates 

from 
./boilersaas/src/boilersaas/templates
to
./web/templates 


and then edit them there.


# Quick memo for myself

Build then publish the package on Pypi:

```python setup.py sdist bdist_wheel```

```twine upload dist/* --v  ``` 

# Still here ??

Thank you then.