from .boundingbox import Boundingbox

class Segment:
    def __init__(self, id, truth, segment_type, traces):
        self.id = id
        self.traces = traces
        self.boundingbox = Boundingbox(traces)
        self.truth = truth
        self.type = segment_type

    def to_latex(self):
        return self.truth


class Group:
    def __init__(self, id, traces):
        self.id = id
        self.traces = traces
        self.boundingbox = Boundingbox(traces)
        self.truth = 'group'
        self.type = 'group'
            
    def to_latex(self):

        latex = ''

        if type(self) == Fraction:
            
            latex += '\\frac{'
            
            for obj in self.numerator:
                latex += obj.to_latex()

            latex += '}{'

            for obj in self.denominator:
                latex += obj.to_latex()

            latex += '}'

        elif type(self) == Power:
            
            for obj in self.base:   
                latex += obj.to_latex()

            latex += '^{'
            
            for obj in self.exponent:
                latex += obj.to_latex()
            
            latex += '}'

        elif type(self) == Root:

            latex += '\\sqrt{'

            for obj in self.core:
                latex += obj.to_latex()

            latex += '}'

        return latex

        
class Fraction(Group):
    def __init__(self, id, numerator, denominator, frac_traces):

        traces = frac_traces
        for obj in numerator:
            traces += obj.traces

        for obj in denominator:
            traces += obj.traces

        super().__init__(id, traces)
        self.numerator = numerator
        self.denominator = denominator

    def to_latex(self):
        return super().to_latex()


class Power(Group):
    def __init__(self, id, base, exponent):

        traces = []

        for obj in base: 
            traces += obj.traces

        for obj in exponent:
            traces += obj.traces

        super().__init__(id, traces)
        self.base = base
        self.exponent = exponent

    def to_latex(self):
        return super().to_latex()


class Root(Group):
    def __init__(self, id, core, root_traces):

        traces = root_traces
        for obj in core:
            traces += obj.traces
            
        super().__init__(id, traces)
        self.core = core

    def to_latex(self):
        return super().to_latex()
