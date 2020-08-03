# Some weirdness goes on with versions of the states
try:
    from localflavor.us.us_states import US_STATES
except ImportError:
    from localflavor.us.us_states import CONTIGUOUS_STATES, NON_CONTIGUOUS_STATES
    US_STATES = CONTIGUOUS_STATES + NON_CONTIGUOUS_STATES


__all__ = ['US_STATES']
