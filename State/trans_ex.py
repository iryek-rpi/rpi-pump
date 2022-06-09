from transitions import Machine, State
import random

class Superhero(object):

    states = ['asleep', 'hanging out', 'hungry', 'sweaty', 'saving the world']

    def __init__(self, name):

        self.name = name
        self.kittens_rescued = 0

        self.machine = Machine(model=self, states=Superhero.states, initial='asleep')

        # Add some transitions. We could also define these using a static list of
        # dictionaries, as we did with states above, and then pass the list to
        # the Machine initializer as the transitions= argument.
        self.machine.add_transition(trigger='wake_up', source='asleep', dest='hanging out')
        self.machine.add_transition('work_out', 'hanging out', 'hungry')
        self.machine.add_transition('eat', 'hungry', 'hanging out')
        self.machine.add_transition('distress_call', '*', 'saving the world',
                         before='change_into_super_secret_costume')
        self.machine.add_transition('complete_mission', 'saving the world', 'sweaty',
                         after='update_journal')

        self.machine.add_transition('clean_up', 'sweaty', 'asleep', conditions=['is_exhausted'])
        self.machine.add_transition('clean_up', 'sweaty', 'hanging out')

        self.machine.add_transition('nap', '*', 'asleep')

    def update_journal(self):
        """ Dear Diary, today I saved Mr. Whiskers. Again. """
        self.kittens_rescued += 1

    @property
    def is_exhausted(self):
        """ Basically a coin toss. """
        return random.random() < 0.5

    def change_into_super_secret_costume(self):
        print("Beauty, eh?")


# Our old Matter class, now with  a couple of new methods we
# can trigger when entering or exit states.
class Matter(object):
    def say_hello(self): print("hello, new state!")
    def say_goodbye(self): print("goodbye, old state!")

lump = Matter()

# Same states as above, but now we give StateA an exit callback
states = [
    State(name='solid', on_exit=['say_goodbye'], on_enter=['say_hello']),
    'liquid',
    { 'name': 'gas', 'on_exit': ['say_goodbye']}
    ]

machine = Machine(lump, states=states, initial='solid')