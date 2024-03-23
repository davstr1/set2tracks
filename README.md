

# Who cares
Probably nobody at this point. I'm not promoting this thing thing either.
I'm writting this for myself, but i have some manners, so it would hurt me to serve the curious soul a blank README.

# About
Ok so i didn't find something for flask that lets you straight out of the box like a pip install and a config file,
then booom you have fully functioning user registration, payment integration, tailwindcss, pre template for logo, landing page and dashboard, so you can **just care about building the damn MVP for your SAAS**. (which is more than enough of a job for a man)
I mean something free, intented at code savy guys, and with no AI cowbells and gimmicks.


# Warning : MVP !

Yes, So far this is an MVP, so no tests, no rainbows or wonderfull CI/CD pipeline...
Also, not written by an expert python wizard, even if i have coding skills, not the best at this, and learning as i go.
Projet gives me a tiggling sense i should be ashamed of it, which is good for an MVP they say.
Plus it "works on my machine", and my mum loves it so shut up and dance.

# Working on my machine so far
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

# Usage
git clone or just download the stuff
pip install -r > requirements.txt.
python run.py
(Delete the boilerplate folder. It's included only for those who want to develop it, But here it's installed as a pip package)

# Usage for devs
if you want to contribute to the repo, or modify the boilerplate.

git clone 
pip install -r > requirements_dev.txt.
pip install -e ./boilersaas

python run.py








pip install -e ./flask_boilerapp

pip install flask_boilersaas==0.1 --extra-index-url https://git.fury.io/davstr1/flask-boilersaas.git


twine upload dist/* --v   