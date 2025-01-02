from dataclasses import dataclass
from typing import List, Dict, Optional
from flask import Flask, request, jsonify
import random
import math
from hidden_markov_model import MathConceptHMM
import numpy as np


@dataclass
class Concept:
    name: str
    keywords: List[str]
    prerequisites: List[str]
    difficulty: float
    probability: float
    template_params: Dict[str, List[float]]

class MathKnowledgeBase:
    def __init__(self):
        self.network = {}
        self._initialize_concepts()
        self._build_network()
        self.hmm_model = MathConceptHMM(self)
        self.test_generator = PracticeTestGenerator(self)
    
    
    def _initialize_concepts(self):
        self.concepts = {
        # Arithmetic
        'basic_arithmetic': Concept(
            name='basic_arithmetic',
            keywords=['add', 'subtract', 'multiply', 'divide' , 'sum', 'difference', 'product', 
                      'quotient', 'calculate', 'compute', 'evaluate', 'operation' , "+" , "-" , "*" , "/"],
            prerequisites=[],
            difficulty=0.2,
            probability=0.4,
            template_params={'a': [1, 100], 'b': [1, 100]}
        ),
        
        # Algebra
        'linear_equations': Concept(
            name='linear_equations',
            keywords=['linear', 'x', 'variable', 'constant', 
                      'unknown', 'expression', 'linear equation'],
            prerequisites=['basic_arithmetic'],
            difficulty=0.4,
            probability=0.3,
            template_params={'a': [-10, 10], 'b': [-20, 20], 'c': [-50, 50]}
        ),
        'quadratic_equations': Concept(
            name='quadratic_equations',
            keywords=['quadratic', 'second degree', 'square', 'squared', 
                      'roots', '^2', 'polynomial' , "x^2"],
            prerequisites=['linear_equations'],
            difficulty=0.6,
            probability=0.4,
            template_params={'a': [-5, 5], 'b': [-10, 10], 'c': [-15, 15]}
        ),
        
        # Geometry
        'geometry_basics': Concept(
            name='geometry_basics',
            keywords=['angle', 'triangle', 'circle', 'rectangle', 'perimeter', 'area', 'circumference', 
                      'radius', 'height', 'width', 'length', 'square', 'measure', 'compute'],
            prerequisites=['basic_arithmetic'],
            difficulty=0.4,
            probability=0.4,
            template_params={'side': [1, 20], 'radius': [1, 15], 'height': [1, 20], 'width': [1, 20]}
        ),
        
        'trigonometry': Concept(
            name='trigonometry',
            keywords=['sin', 'cos', 'tan', 'angle', 'triangle', 'hypotenuse', 'opposite', 'adjacent', 'sine', 
                      'cosine', 'tangent', 'cotangent', 'cosecant', 'secant', 'cot', 'csc', 'sec', 'right triangle', 
                      'calculate', 'evaluate'],
            prerequisites=['geometry_basics'],
            difficulty=0.7,
            probability=0.875,
            template_params={'angle': [0, 360], 'side': [1, 20]}
        ),
        
        # Calculus
        'derivatives': Concept(
            name='derivatives',
            keywords=['derivative','derivate' , 'rate of change', 'differentiate', 'slope', 'tangent line', 'function', 
                      'd/dx', 'dx', 'dy/dx', 'calculus', 'instantaneous rate', 'evaluate'],
            prerequisites=['quadratic_equations', 'trigonometry'],
            difficulty=0.8,
            probability=0.9,
            template_params={'a': [-5, 5], 'b': [-10, 10], 'n': [2, 4]}
        ),
        'integrals': Concept(
            name='integrals',
            keywords=['integral', 'antiderivative', 'integrate', 'area under curve', 'definite integral', 
                      'indefinite integral', 'integration', 'evaluate', 'calculus', 'dx', '∫', 'limits'],
            prerequisites=['derivatives'],
            difficulty=0.9,
            probability=0.9,
            template_params={'a': [-5, 5], 'b': [-10, 10], 'n': [2, 4]}
        )
    }
    
    def _build_network(self):
        for concept_name, concept in self.concepts.items():
            self.network[concept_name] = {'children': [], 'parents': concept.prerequisites}
            for prereq in concept.prerequisites:
                if prereq in self.network:
                    self.network[prereq]['children'].append(concept_name)
                else:
                    self.network[prereq] = {'children': [concept_name], 'parents': []}

    def analyze_question(self, question: str) -> Dict:
        return self.hmm_model.analyze_question(question)
    
    def generate_practice_test(self, concepts: List[str], num_questions: int = 10) -> Dict:
        """Generate practice tests for the top probability concept"""
        if len(concepts) == 0:
            raise ValueError("Concepts list must not be empty.")
        
        # Find the concept with the highest probability
        top_concept = concepts[0]
        
        # Generate questions for the top probability concept and its prerequisites
        test = self.test_generator.generate_practice_test(
            concept=top_concept,
            num_questions=num_questions,
            include_prerequisites=False
        )
        
        return {
            'tests': [test],
            'total_questions': test['num_questions'],
            'concepts_covered': [top_concept] + self.concepts[top_concept].prerequisites
        }
        
# ---------------------------------------------------------------------------------------

from typing import List, Dict, Set, Tuple
import random
import heapq
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class TestQuestion:
    question: str
    concept: str
    prerequisites: List[str]
    expected_answer: str
    template_used: str

class PracticeTestGenerator:
    def __init__(self, knowledge_base: MathKnowledgeBase):
        self.kb = knowledge_base
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize question templates for each concept"""
        self.templates = {
            'basic_arithmetic': [
                "Calculate {a} {op} {b}",
                "What is the result of {a} {op} {b}?",
                "Evaluate the expression: {a} {op} {b}",
            ],
            'linear_equations': [
                "Solve for x: {a}x + {b} = {c}",
                "Find x: {a}x = {b}",
                "What value of x satisfies {a}x + {b} = {c}?",
            ],
            'quadratic_equations': [
                "Solve the quadratic equation: {a}x² + {b}x + {c} = 0",
                "Find the roots of {a}x² + {b}x + {c} = 0",
                "Determine the values of x: {a}x² + {b}x = {-c}",
            ],
            'geometry_basics': [
                "Find the area of a rectangle with width {width} and height {height}",
                "Calculate the circumference of a circle with radius {radius}",
                "What is the perimeter of a square with side length {side}?",
            ],
            'trigonometry': [
                "Find sin({angle}°) to 2 decimal places",
                "In a right triangle with hypotenuse {c} and angle {angle}°, find the opposite side",
                "Calculate tan({angle}°) to 2 decimal places",
            ],
            'derivatives': [
                "Find d/dx [{a}x^{n} + {b}x]",
                "Calculate the derivative of {a}x^{n} + {b}x",
                "What is the slope of the tangent line to f(x) = {a}x^{n} at x = {b}?",
            ],
            'integrals': [
                "Evaluate ∫({a}x^{n} + {b})dx",
                "Calculate the definite integral of {a}x^{n} from 0 to {b}",
                "Find ∫[{a}x^{n} - {b}x]dx",
            ],
        }

    def _generate_answer(self, template: str, params: Dict, concept: str) -> str:
        """Generate expected answer based on template and parameters"""
        if concept == 'basic_arithmetic':
            if 'op' in params:
                if params['op'] == '+': return str(params['a'] + params['b'])
                if params['op'] == '-': return str(params['a'] - params['b'])
                if params['op'] == '*': return str(params['a'] * params['b'])
                if params['op'] == '/': return f"{params['a'] / params['b']:.2f}"
                
        elif concept == 'linear_equations':
            if 'Solve' in template:
            # ax + b = c -> x = (c-b)/a
                return f"x = {(params['c'] - params['b']) / params['a']:.2f}"
            elif 'Find' in template:
                # ax = b -> x = b/a
                return f"x = {params['b'] / params['a']:.2f}"
            elif 'value' in template:
                return f"x = {(params['c'] - params['b']) / params['a']:.2f}"
        
        
        elif concept == 'quadratic_equations':
            # Using quadratic formula
            a, b, c = params['a'], params['b'], params['c']
            disc = b**2 - 4*a*c
            if disc < 0:
                return "No real solutions"
            elif disc == 0:
                return f"x = {-b/(2*a):.2f}"
            else:
                x1 = (-b + disc**0.5)/(2*a)
                x2 = (-b - disc**0.5)/(2*a)
                return f"x = {x1:.2f} or x = {x2:.2f}"
            
        elif concept == 'geometry_basics':
            if 'width' in params and 'height' in params:
                return str(params['width'] * params['height'])
            if 'radius' in params:
                return f"{2 * math.pi * params['radius']:.2f}"
            if 'side' in params:
                return str(4 * params['side'])
    
        elif concept == 'trigonometry':
            if 'angle' in params:
                angle_rad = math.radians(params['angle'])
                if 'sin' in template:
                    return f"{math.sin(angle_rad):.2f}"
                if 'cos' in template:
                    return f"{math.cos(angle_rad):.2f}"
                if 'tan' in template:
                    return f"{math.tan(angle_rad):.2f}"
            if 'c' in params and 'angle' in params:
                angle_rad = math.radians(params['angle'])
                return f"{params['c'] * math.sin(angle_rad):.2f}"
        
        elif concept == 'derivatives':
            if 'a' in params and 'n' in params:
                return f"{params['a'] * params['n']}x^{params['n'] - 1} + {params['b']}"
        
        elif concept == 'integrals':
            if 'a' in params and 'n' in params:
                return f"({params['a'] / (params['n'] + 1)}x^{params['n'] + 1} + {params['b']}x) + C"
                    
        return "Solution process required"

    def _generate_parameters(self, concept: str) -> Dict:
        """Generate random parameters for a question template"""
        concept_data = self.kb.concepts[concept]
        params = {}
        for param, range_vals in concept_data.template_params.items():
            min_val, max_val = range_vals
            params[param] = random.randint(min_val, max_val)
        
        if concept == 'basic_arithmetic':
            params['op'] = random.choice(['+', '-', '*', '/'])
        
        return params

    def generate_practice_test(self, 
                             concept: str, 
                             num_questions: int = 10, 
                             include_prerequisites: bool = True) -> Dict:
        """Generate a complete practice test for a concept"""
        test_questions = []
        concepts_to_cover = [concept]
        
        # Include prerequisites if requested
        if include_prerequisites:
            current = concept
            while self.kb.concepts[current].prerequisites:
                for prereq in self.kb.concepts[current].prerequisites:
                    if prereq not in concepts_to_cover:
                        concepts_to_cover.append(prereq)
                current = self.kb.concepts[current].prerequisites[0]
        
        # Calculate number of questions per concept
        total_concepts = len(concepts_to_cover)
        questions_per_concept = {
            c: max(2, num_questions // total_concepts)
            for c in concepts_to_cover
        }
        questions_per_concept[concept] += num_questions - sum(questions_per_concept.values())
        
        # Generate questions
        for c in concepts_to_cover:
            num = questions_per_concept[c]
            
            for _ in range(num):
                template = random.choice(self.templates[c])
                params = self._generate_parameters(c)
                
                # Ensure all required parameters are present
                try:
                    question = template.format(**params)
                except KeyError as e:
                    print(f"Missing parameter {e} for concept {c}. Skipping question.")
                    continue
                
                answer = self._generate_answer(template, params, c)
                test_questions.append(TestQuestion(
                    question=question,
                    concept=c,
                    prerequisites=self.kb.concepts[c].prerequisites,
                    expected_answer=answer,
                    template_used=template
                ))
        
        return {
            'concept': concept,
            'num_questions': len(test_questions),
            'includes_prerequisites': include_prerequisites,
            'questions': [
                {
                    'question': q.question,
                    'concept': q.concept,
                    'prerequisites': q.prerequisites,
                    'expected_answer': q.expected_answer
                }
                for q in test_questions
            ],
            'concepts_covered': concepts_to_cover
        }
        
        
# ------------------------------------------------------------

from flask import Flask, request, jsonify
from flask_cors import CORS

knowledge_base = MathKnowledgeBase()

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    question = data.get('question', '')
    result = knowledge_base.analyze_question(question)
    print(result)
    return jsonify(result)

@app.route('/generate_test', methods=['POST'])
def generate_test():
    data = request.get_json()
    concepts = data.get('concepts', [])
    num_questions = data.get('num_questions', 10)
    
    practice_test = knowledge_base.generate_practice_test(
        concepts=concepts,
        num_questions=num_questions
    )
    print(practice_test)
    
    return jsonify(practice_test)

if __name__ == '__main__':
    app.run(debug=True)