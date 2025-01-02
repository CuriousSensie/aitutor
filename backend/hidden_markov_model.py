import re
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

@dataclass
class HMMParams:
    states: List[str]  # Concepts
    observations: List[str]  # Keywords and patterns
    start_probabilities: Dict[str, float]
    transition_matrix: Dict[str, Dict[str, float]]
    emission_matrix: Dict[str, Dict[str, float]]

class MathConceptHMM:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.hmm_params = self._initialize_hmm()
        self._compile_observation_patterns()

    
    def _initialize_hmm(self) -> HMMParams:
        states = list(self.kb.concepts.keys())
        observations = set()
        for concept in self.kb.concepts.values():
            observations.update(concept.keywords)
        observations = list(observations)
        print("Observations: ", observations)
        
        total_prob = sum(
            concept.probability if concept.probability > 0 else (1 - concept.difficulty)
            for concept in self.kb.concepts.values()
        )
        
        # Initialize start probabilities and normalize them
        start_probabilities = {
            name: (concept.probability / total_prob) if concept.probability > 0 else ((1 - concept.difficulty) / total_prob)
            for name, concept in self.kb.concepts.items()
        }
        
        transition_matrix = {}
        for from_state in states:
            transition_matrix[from_state] = {}
            children = set(self.kb.network[from_state]['children'])
            parents = set(self.kb.network[from_state]['parents'])
            connected_states = children.union(parents)
            
            base_prob = 0.1 / (len(states) - 1)
            connected_prob = 0.9 / max(len(connected_states), 1)
            
            for to_state in states:
                concept_prob = self.kb.concepts[to_state].probability if self.kb.concepts[to_state].probability > 0 else 1.0
                if to_state == from_state:
                    transition_matrix[from_state][to_state] = 0.7 * concept_prob
                elif to_state in connected_states:
                    transition_matrix[from_state][to_state] = connected_prob * 0.3 * concept_prob
                else:
                    transition_matrix[from_state][to_state] = base_prob * 0.3 * concept_prob
        
        emission_matrix = {}
        for state in states:
            emission_matrix[state] = {}
            concept = self.kb.concepts[state]
            scaling_factor = concept.probability if concept.probability > 0 else 1.0

            for obs in observations:
                if obs in concept.keywords:
                    emission_matrix[state][obs] = (0.8 / len(concept.keywords)) * scaling_factor
                else:
                    emission_matrix[state][obs] = (0.2 / (len(observations) - len(concept.keywords))) * scaling_factor
        
        return HMMParams(
            states=states,
            observations=observations,
            start_probabilities=start_probabilities,
            transition_matrix=transition_matrix,
            emission_matrix=emission_matrix
        )

    def _compile_observation_patterns(self):
        self.patterns = {}
        for obs in self.hmm_params.observations:
            pattern = r'\b' + re.escape(obs) + r'\b'
            self.patterns[obs] = re.compile(pattern, re.IGNORECASE)
        
        self.special_patterns = {
            'equation': re.compile(r'[^><=]=(?!=)'),
            'inequality': re.compile(r'[<>]=?|!='),
            'squared': re.compile(r'\b\w+\^2\b|²'),
            'fraction': re.compile(r'/|\bover\b|\bdivided by\b'),
            'function': re.compile(r'\b[fg]\(.*?\)'),
        }

    def _extract_observations(self, question: str) -> List[str]:
        observations = []
        for obs, pattern in self.patterns.items():
            if pattern.search(question):
                observations.append(obs)
        for obs_type, pattern in self.special_patterns.items():
            if pattern.search(question):
                observations.append(obs_type)
        # Handle operand-only input (numbers and basic operators)
        if not observations:
            if re.search(r'\b\d+\b', question):  # Check if the question contains numbers
                observations.append('operand')  # Add a generic observation for operands
        return observations


    def viterbi(self, observations: List[str]) -> Tuple[float, List[str]]:
        V = [{}]
        path = {}
        for state in self.hmm_params.states:
            V[0][state] = self.hmm_params.start_probabilities[state] * \
                         self.hmm_params.emission_matrix[state].get(observations[0], 1e-10)
            path[state] = [state]
        
        for t in range(1, len(observations)):
            V.append({})
            newpath = {}
            for curr_state in self.hmm_params.states:
                max_prob, best_state = max(
                    (V[t-1][prev_state] * \
                     self.hmm_params.transition_matrix[prev_state][curr_state] * \
                     self.hmm_params.emission_matrix[curr_state].get(observations[t], 1e-10),
                     prev_state)
                    for prev_state in self.hmm_params.states
                )
                V[t][curr_state] = max_prob
                newpath[curr_state] = path[best_state] + [curr_state]
            path = newpath
        
        prob, best_final_state = max((V[-1][state], state) for state in self.hmm_params.states)
        return prob, path[best_final_state]

    def analyze_question(self, question: str) -> Dict:
        observations = self._extract_observations(question.lower())
        if not observations:
            return {
                'error': 'No relevant patterns found in question',
                'concepts': []
            }
        # Handle operand-only case
        if observations == ['operand']:
            return {
                'main_concept': 'basic_arithmetic',
                'confidence': 1.0,
                'prerequisites': [],
                'related_concepts': [{'concept': 'basic_arithmetic', 'probability': 1.0, 'difficulty': 0.2}],
                'observations': observations
            }
            
        prob, state_sequence = self.viterbi(observations)
        final_concept = state_sequence[-1]
        prerequisites = self.kb.concepts[final_concept].prerequisites
        
        related_concepts = []
        total_score = 0
        for concept in self.hmm_params.states:
            emission_score = np.mean([
                self.hmm_params.emission_matrix[concept].get(obs, 1e-10)
                for obs in observations
            ])
            if len(state_sequence) > 1:
                prev_state = state_sequence[-2]
                transition_score = self.hmm_params.transition_matrix[prev_state][concept]
            else:
                transition_score = self.hmm_params.start_probabilities[concept]
            score = emission_score * transition_score
            total_score += score
            related_concepts.append({
                'concept': concept,
                'probability': score,
                'difficulty': self.kb.concepts[concept].difficulty
            })
        
        for concept in related_concepts:
            concept['probability'] /= total_score
        related_concepts.sort(key=lambda x: x['probability'], reverse=True)
        
        # print('main_concept': final_concept,
        #     'confidence': prob,
        #     'prerequisites': prerequisites,
        #     'related_concepts': related_concepts,
        #     'observations': observations)
        
        return {
            'main_concept': final_concept,
            'confidence': prob,
            'prerequisites': prerequisites,
            'related_concepts': related_concepts,
            'observations': observations
        }