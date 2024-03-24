

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
## General

### 1 - Get the thing, yes

`gh repo clone davstr1/flask-boilersaas`

 or just download it.

### 2 - Install and run Tailwind
install tailwind stuff with npm

`npm i tailwindcss`

Then launch the tailwind watcher.
This will watch for the css we use and add/remove them from our css/output.css
( Go and learn a bit about Tailwind if you have to)

`npx tailwindcss -i ./web/app/static/css/input.css -o ./web/app/static/css/output.css --watch`

### 3 - Install python dependencies

`pip install -r web/requirements.txt`


### 4 - Edit environment variables

Copy example.env into a .env, and fill it with your data.


### 5 - Proudly run the app

`python run.py`

### Notes

- PROD : You can the boilerplate folder. It's included only for developping the package, and copying the templates. (See styling and templates) 
All you really need in prod is the content of the "web" folder.


- You can rename "web" to your likings, 
just also change the npx command accordingly.

## Usage for devs
if you want to contribute to the repo, or modify the boilerplate.


Same process, except instead of #3 

You don't pip install the boilersaas from Pypi,
but do an editable install instead :

`pip install -r  exampler_app/requirements_dev.txt` 

`pip install -e ./boilersaas`

Now you can edit ./boilersaas and see immediate results.


# Styling and Templates

The templates are in the pip package (boilerplate)
Like login, registration, header etc..
But you can overwrite anything, just copying the corresponding templates 

from 
`./boilersaas/src/boilersaas/templates `
to
`./web/templates 
`

and then edit it there.






## Quick memo for myself

Build then publish the package on Pypi:

`python setup.py sdist bdist_wheel`

`twine upload dist/* --v  ` 

# Still here ??

Thank you then.