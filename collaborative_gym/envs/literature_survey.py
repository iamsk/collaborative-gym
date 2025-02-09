import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from io import BytesIO
from typing import Any, Union, Optional

import arxiv
import dspy
import knowledge_storm
import requests
from PyPDF2 import PdfReader
from knowledge_storm import ArticleTextProcessing
from knowledge_storm.lm import OpenAIModel, LitellmModel

from collaborative_gym.core import CoEnv, ObservationTypes, logger
from collaborative_gym.envs.registry import EnvFactory
from collaborative_gym.spaces import (
    MAX_UNICODE_LENGTH,
    UnicodeWithRegexPattern,
    MultiSpace,
)
from collaborative_gym.utils.retriever import ArxivRetriever
from collaborative_gym.utils.string import post_process_parsed_function_arg
from collaborative_gym.utils.text_editor import TextEditor
from collaborative_gym.utils.utils import prepare_lm_kwargs


class LitSurveyActions(Enum):
    SEARCH_ARXIV = "SEARCH_ARXIV"
    LIBRARY_TO_DRAFT = "LIBRARY_TO_DRAFT"
    POLISH_DRAFT_WITH_LIBRARY = "POLISH_DRAFT_WITH_LIBRARY"
    ADD_PAPER_TO_LIBRARY = "ADD_PAPER_TO_LIBRARY"
    DROP_PAPER_FROM_LIBRARY = "DROP_PAPER_FROM_LIBRARY"
    EDITOR_UPDATE = "EDITOR_UPDATE"
    FINISH = "FINISH"

    def __str__(self):
        """Overrides the default string representation of the Enum by returning the value."""
        return self.value


class WriteRelatedWorks(dspy.Signature):
    """Write a concise and focused related works section for an academic research paper on the given topic, using the provided list of papers and their accompanying notes.
    Criteria:
    1. Length and Conciseness: The related works section should be concise and not overly elaborate.
    2. Theme-Based Organization: Identify key themes, trends, or research directions within the provided literature. Organize the related works section by these themes rather than by simply enumerating individual papers.
    4. Use of Provided Notes: Leverage the notes accompanying each paper to draw connections between studies.
    5. Logical Flow and Cohesion: Create a logical progression of ideas that guides the reader through the themes. Employ headings and subheadings to divide the section into manageable, thematic parts.
    6. Academic Writing Style: Write in a clear, concise, and formal academic tone.
    7. Citations: Add inline citations to the papers in the provided list.

    Here is the format of your writing:
    Use [1], [2], ..., [n] in line (for example, "The capital of the United States is Washington, D.C.[1][3]."). You DO NOT need to include a References or Sources section to list the sources at the end.
    """

    query = dspy.InputField(
        prefix="The topic of the paper the related works section is being written for: ",
        format=str,
    )
    papers = dspy.InputField(
        prefix="The list of papers you can use in the related works section: ",
        format=str,
    )
    example_related_works = dspy.InputField(
        prefix="Example related works section: ", format=str
    )
    output = dspy.OutputField(
        prefix="Write the related work section with proper inline citations (Start your writing directly):\n",
        format=str,
    )


class WritingRelatedWorksModule(dspy.Module):
    """Creates a draft of the related works"""

    def __init__(
        self,
        lm: Union[dspy.dsp.LM, dspy.dsp.HFModel, knowledge_storm.lm.LM],
    ):
        super().__init__()
        self.create_related_works = dspy.Predict(WriteRelatedWorks)
        self.text_processor = ArticleTextProcessing()
        self.engine = lm

    def forward(self, query: str, papers: list, example: str):
        max_word_cnt_per_paper = 4000 / len(papers) if len(papers) > 0 else 4000
        concatenated_papers = ""
        idx = 0
        for paper in papers:
            idx += 1
            concatenated_papers += (
                self.text_processor.limit_word_count_preserve_newline(
                    input_string=f"[{idx}] paper['title']"
                    + "\n"
                    + "\n".join([f"- {s}" for s in paper["notes"]])
                    + "\n",
                    max_word_count=max_word_cnt_per_paper,
                )
            )

        with dspy.settings.context(lm=self.engine, show_guidelines=False):
            related_works = self.create_related_works(
                query=query,
                papers="\n".join(concatenated_papers),
                example_related_works=example,
            ).output
        if "Related Works" in related_works:
            related_works = (
                related_works.split("Related Works")[1]
                .strip()
                .strip("\n")
                .strip("*")
                .strip("\n")
            )

        return related_works


class PolishRelatedWorks(dspy.Signature):
    """Polish the related works section based on the polishing request and the provided list of papers with their accompanying notes.
    Criteria:
    1. Length and Conciseness: The related works section should be concise and not overly elaborate.
    2. Theme-Based Organization: Identify key themes, trends, or research directions within the provided literature. Organize the related works section by these themes rather than by simply enumerating individual papers.
    4. Use of Provided Notes: Leverage the notes accompanying each paper to draw connections between studies.
    5. Logical Flow and Cohesion: Create a logical progression of ideas that guides the reader through the themes. Employ headings and subheadings to divide the section into manageable, thematic parts.
    6. Academic Writing Style: Write in a clear, concise, and formal academic tone.
    7. Citations: Add inline citations to the papers in the provided list.

    Here is the format of your writing:
    Use [1], [2], ..., [n] in line (for example, "The capital of the United States is Washington, D.C.[1][3]."). You DO NOT need to include a References or Sources section to list the sources at the end.
    """

    papers = dspy.InputField(
        prefix="The list of papers you can use in the related works section: ",
        format=str,
    )
    current_draft = dspy.InputField(prefix="Current Draft: ", format=str)
    polishing_request = dspy.InputField(prefix="Polishing Request: ", format=str)
    output = dspy.OutputField(
        prefix="Polished draft with proper inline citations (Start your writing directly):\n",
        format=str,
    )


class PolishingRelatedWorksModule(dspy.Module):
    """Polish the draft of the related works based on the polishing request"""

    def __init__(
        self,
        lm: Union[dspy.dsp.LM, dspy.dsp.HFModel, knowledge_storm.lm.LM],
    ):
        super().__init__()
        self.polish_related_work = dspy.Predict(PolishRelatedWorks)
        self.text_processor = ArticleTextProcessing()
        self.engine = lm

    def forward(self, papers: list, current_draft: str, polishing_request: str):
        max_word_cnt_per_paper = 4000 / len(papers) if len(papers) > 0 else 4000
        concatenated_papers = ""
        idx = 0
        for paper in papers:
            idx += 1
            concatenated_papers += (
                self.text_processor.limit_word_count_preserve_newline(
                    input_string=f"[{idx}] paper['title']"
                    + "\n"
                    + "\n".join([f"- {s}" for s in paper["notes"]])
                    + "\n",
                    max_word_count=max_word_cnt_per_paper,
                )
            )

        with dspy.settings.context(lm=self.engine, show_guidelines=False):
            related_works = self.polish_related_work(
                papers="\n".join(concatenated_papers),
                current_draft=current_draft,
                polishing_request=polishing_request,
            ).output
        if "Related Works" in related_works:
            related_works = (
                related_works.split("Related Works")[1]
                .strip()
                .strip("\n")
                .strip("*")
                .strip("\n")
            )

        return related_works


class ExtractNotes(dspy.Signature):
    """Given the following paper, provide 5 concise and comprehensive notes that can later be used to write a related works in a paper with a similar topic to the given paper. Your notes may include
    1. Summaries of the relevant portions of the papers
    2. Exact text extraction of parts of the paper that would be important to include in a related works section
    3. Key Insights that you draw from the paper that would be helpful to include in a related works section
    You are restricted to take 5 notes to ensure that the notes are concise and focused.
    Output note in the following format:
    - note 1
    - note 2
    - note 3
    - note 4
    - note 5
    """

    paper = dspy.InputField(prefix="Paper: ", format=str)
    output = dspy.OutputField(
        prefix="Notes (Please strictly follow the output format):\n", format=str
    )


class ExtractNotesModule(dspy.Module):
    """Generate notes on a given paper"""

    def __init__(
        self,
        lm: Union[dspy.dsp.LM, dspy.dsp.HFModel, knowledge_storm.lm.LM],
    ):
        super().__init__()
        self.extract_notes = dspy.Predict(ExtractNotes)
        self.engine = lm

    def forward(self, paper_link: str):
        response = requests.get(paper_link)
        response.raise_for_status()
        pdf_file = BytesIO(response.content)
        pdf_content = ""

        reader = PdfReader(pdf_file)
        number_of_pages = len(reader.pages)

        for page_num in range(
            min(2, number_of_pages)
        ):  # Only process the first two pages to speed up.
            page = reader.pages[page_num]
            text = page.extract_text()
            pdf_content += text

        notes = []
        with dspy.settings.context(lm=self.engine, show_guidelines=False):
            output = self.extract_notes(paper=pdf_content).output
            for note in output.split("\n"):
                note = note.strip()
                if note and note[0] == "-":
                    notes.append(note[1:].strip())

        return notes


@EnvFactory.register("lit_survey")
class CoLitSurveyEnv(CoEnv):
    """
    ## Description
    CoLitSurveyEnv is an environment for conducting literature survey (e.g., writing Related Work section for research). The environment supports
    searching for papers, taking notes, and writing/polishing a related works section.

    ## Action Space
    Actions are strings that must match one of the following patterns:
    - SEARCH_ARXIV(query: str): Search for papers on arXiv
    - ADD_PAPER_TO_LIBRARY(paper_id: str): Add a paper to the working library
    - DROP_PAPER_FROM_LIBRARY(paper_id: str): Remove a paper from the library
    - LIBRARY_TO_DRAFT(example: str): Generate a draft of the related works section
    - POLISH_DRAFT_WITH_LIBRARY(polishing_request: str): Polish the draft based on the polishing request
    - EDITOR_UPDATE(text: str): Update the editor content
    - FINISH(): Complete the current task

    ## Observation Space
    The observation is a dictionary containing:
    - library (non-private): List of papers in the working library with their metadata
    - related_works_editor (non-private): The current content of the related works editor
    - search_window (private): The search results from the last search action
    """

    def __init__(
        self,
        team_members: list[str],
        env_id: str,
        use_simulated_dataset: bool = False,
        query: Optional[str] = None,
        simulated_data_point_idx: Optional[int] = None,  # [0, 1, ..., 99]
        simulated_data_path="datasets/RelatedWorkWriting/test.json",
        rubric_path="datasets/RelatedWorkWriting/rubric.txt",
        parsing_model: str = "gpt-4o-mini",
        writing_model: str = "gpt-4o-2024-08-06",
    ):
        super().__init__(team_members=team_members, env_id=env_id)

        self.use_simulated_dataset = use_simulated_dataset
        self.rubric_path = rubric_path
        try:
            # The evaluator could be changed to a different model.
            # Use OpenAI GPT to match the Collaborative Gym paper.
            self.evaluator_lm = OpenAIModel(
                model="gpt-4-0613",
                api_key=os.environ["OPENAI_API_KEY"],
            )
        except KeyError:
            self.evaluator_lm = None
            logger.error(
                "Please provide your OpenAI API key in the environment variable OPENAI_API_KEY to enable the evaluator."
            )

        self.retrieve_top_k = 10
        if self.use_simulated_dataset:
            try:
                self.paper_retriever = ArxivRetriever(
                    voyage_api=os.environ["VOYAGE_API_KEY"],
                    qdrant_endpoint=os.environ["QDRANT_ENDPOINT"],
                    qdrant_api=os.environ["QDRANT_API_KEY"],
                    qdrant_collection_name=os.environ["QDRANT_COLLECTION"],
                    retrieve_top_k=self.retrieve_top_k,
                )
            except KeyError:
                self.paper_retriever = None
                logger.error(
                    "Please provide your Voyage API key in the environment variable VOYAGE_API_KEY, "
                    "Qdrant API key in the environment variable QDRANT_API_KEY, "
                    "Qdrant endpoint in the environment variable QDRANT_ENDPOINT, "
                    "and Qdrant collection name in the environment variable QDRANT_COLLECTION to enable the paper retriever."
                )
            self.simulated_data_point_idx = simulated_data_point_idx
            with open(simulated_data_path) as f:
                self.data_point = json.load(f)[self.simulated_data_point_idx]
            self.query = (
                f"Help me write a related works section for a research paper related to "
                f"{self.data_point['topic']}. "
                f"My current paper title is \"{self.data_point['title']}\". "
                f"The paper falls into the domain of {self.data_point['domain']}."
            )
            # Additional task information
            hidden_info_rh = []  # Required headings
            hidden_info_rp = []  # Required papers
            hidden_info_ps = []  # Previous findings when searching literature
            style_requirements = []
            for h in self.data_point["hidden_requirements"]:
                if h[0] == "RH":
                    hidden_info_rh.append(h[1])
                elif h[0] == "RP":
                    hidden_info_rp.append(h[1])
                elif h[0] == "PS":
                    hidden_info_ps.append(h[1])
                elif h[0] == "NS":
                    if h[1] == 1 or h[1] == 0:
                        style_requirements.append(
                            "Would like to have the related works section as a cohesive "
                            "paragraph without additional headings."
                        )
                    else:
                        style_requirements.append(
                            f"Would like to have {h[1]} headings in the related works section."
                        )
                elif h[0] == "NC":
                    style_requirements.append(
                        f"Would like to have around {h[1]} papers cited in the related works section."
                    )
            self.additional_task_info = {"Style requirements": style_requirements}
            if len(hidden_info_rh) > 0:
                self.additional_task_info["Headings that you want to include"] = (
                    hidden_info_rh
                )
            if len(hidden_info_rp) > 0:
                self.additional_task_info["Papers that you want to include"] = (
                    hidden_info_rp
                )
            if len(hidden_info_ps) > 0:
                self.additional_task_info[
                    "Your previous findings when searching literature that you hope to include"
                ] = hidden_info_ps
        else:
            self.paper_retriever = arxiv.Client()
            self.query = query

        self.task_description = (
            "You are good at academic writing. Your task is to help a user or a group of users write a "
            '"Related Works" section for their research paper given the user\'s initial query.\n'
            "To do this, you must first collect a list of research papers and add them to the shared paper list."
            "Based on the collected papers, you will then write a related works section that synthesizes the "
            "literature. Make sure you include inline citations in your writing and use [1], [2], ..., to match "
            "index of collected papers in the library. Output FINISH() to finish the task.\n"
            "Once finished, your performance will be evaluated "
            'based on the quality and user satisfaction of the "Related Work" section in the editor.\n\n'
            f'The user\'s initial query is "{self.query}".\n'
        )

        try:
            parsing_model_kwargs = prepare_lm_kwargs(parsing_model)
            self.parsing_model = LitellmModel(
                **parsing_model_kwargs,
                max_tokens=2000,
            )
            writing_model_kwargs = prepare_lm_kwargs(writing_model)
            self.writing_model = LitellmModel(
                **writing_model_kwargs,
                max_tokens=10000,
            )
        except KeyError:
            self.parsing_model = None
            self.writing_model = None
            logger.error(
                "Please provide api key that matches your choice of model to enable the parsing and writing models."
            )

        self.extract_notes = ExtractNotesModule(lm=self.parsing_model)
        self.write_related_works_module = WritingRelatedWorksModule(
            lm=self.writing_model
        )
        self.polish_related_works_module = PolishingRelatedWorksModule(
            lm=self.writing_model
        )

        # Private observation
        self.search_window = {
            team_member: {"query": "", "results": []} for team_member in team_members
        }

        # Public observation
        self.related_works_editor = TextEditor()
        self.paper_library = []
        self.paper_library_titles = set()

        # Action space
        self.action_space = MultiSpace(
            (
                UnicodeWithRegexPattern(
                    min_length=0,
                    max_length=MAX_UNICODE_LENGTH,
                    regex_pattern=re.compile(
                        r"^ADD_PAPER_TO_LIBRARY\(titles=(.*), links=(.*)\)$", re.DOTALL
                    ),
                    params=["titles", "links"],
                    machine_readable_identifier=LitSurveyActions.ADD_PAPER_TO_LIBRARY,
                    human_readable_name="Add paper(s) to the shared library",
                    human_readable_description="Add paper(s) to the shared library. Make sure the titles and links "
                    "match in order. The library will automatically "
                    "extract notes from the paper(s) so you don't need to do it manually. "
                    "Papers in the library will be used to write the related works section.",
                ),
                UnicodeWithRegexPattern(
                    min_length=0,
                    max_length=MAX_UNICODE_LENGTH,
                    regex_pattern=re.compile(
                        r"^DROP_PAPER_FROM_LIBRARY\(title=(.*)\)$", re.DOTALL
                    ),
                    params=["title"],
                    machine_readable_identifier=LitSurveyActions.DROP_PAPER_FROM_LIBRARY,
                    human_readable_name="Drop a recommended paper from the shared paper list",
                    human_readable_description="Drop a recommended paper from the shared library based on the title.",
                ),
                UnicodeWithRegexPattern(
                    min_length=0,
                    max_length=MAX_UNICODE_LENGTH,
                    regex_pattern=re.compile(
                        r"^LIBRARY_TO_DRAFT\(example=(.*)\)$", re.DOTALL
                    ),
                    params=["example"],
                    machine_readable_identifier=LitSurveyActions.LIBRARY_TO_DRAFT,
                    human_readable_name="Update the editor with the related works draft based on the papers in the "
                    "library",
                    human_readable_description="Create a related works draft based on the topic and current collected "
                    "papers in the paper library, and the example related work section "
                    "(if `example` is not None). Note that this action will overwrite the "
                    "current content in the editor. If the library is unchanged, the draft "
                    "will be the same as the previous one when calling this function.",
                ),
                UnicodeWithRegexPattern(
                    min_length=0,
                    max_length=MAX_UNICODE_LENGTH,
                    regex_pattern=re.compile(
                        r"^POLISH_DRAFT_WITH_LIBRARY\(polishing_request=(.*)\)$",
                        re.DOTALL,
                    ),
                    params=["polishing_request"],
                    machine_readable_identifier=LitSurveyActions.POLISH_DRAFT_WITH_LIBRARY,
                    human_readable_name="Polish the related works draft based on the polishing request, the papers in "
                    "the library and the current draft.",
                ),
                UnicodeWithRegexPattern(
                    min_length=0,
                    max_length=MAX_UNICODE_LENGTH,
                    regex_pattern=re.compile(
                        r"^EDITOR_UPDATE\(text=(.*)\)$", re.DOTALL
                    ),
                    params=["text"],
                    machine_readable_identifier=LitSurveyActions.EDITOR_UPDATE,
                    human_readable_name="Update the editor with the provided text. The full original text will be "
                    "replaced. Please use this action for small edit to the current text.",
                ),
                UnicodeWithRegexPattern(
                    min_length=0,
                    max_length=MAX_UNICODE_LENGTH,
                    regex_pattern=re.compile(r"^FINISH\(\)$", re.DOTALL),
                    params=[],
                    machine_readable_identifier=LitSurveyActions.FINISH,
                    human_readable_name="Finish writing the related work section",
                    human_readable_description="Finish writing the related work section.",
                ),
            )
        )

        self.private_action_space = MultiSpace(
            (
                UnicodeWithRegexPattern(
                    min_length=0,
                    max_length=MAX_UNICODE_LENGTH,
                    regex_pattern=re.compile(
                        r"^SEARCH_ARXIV\(query=(.*)\)$", re.DOTALL
                    ),
                    params=["query"],
                    machine_readable_identifier=LitSurveyActions.SEARCH_ARXIV,
                    human_readable_name="Search arXiv API given a query",
                    human_readable_description="Given a string query input, searches arXiv API for "
                    "the given query and returns a list of dictionaries "
                    "where each dictionary contains the keys of "
                    '"url", "pdf", and "metadata" which map to '
                    "a url link, pdf link and dictionary of metadata. The search results "
                    "will be stored in the search window.",
                ),
            )
        )

        # An example question and trajectory for team members to understand the task
        self.example_question = (
            'Could you help me write a related works section for "PrivacyLens: Evaluating '
            'Privacy Norm Awareness of Language Models in Action"?'
        )
        self.example_trajectory = [
            (
                "First, search for papers directly related to the topic of the paper.",
                'SEARCH_ARXIV(query="PrivacyLens: Evaluating Privacy Norm Awareness of Language Models in Action")',
                {
                    "search_window": {
                        "query": "PrivacyLens: Evaluating Privacy Norm Awareness of Language Models in Action",
                        "results": [
                            {
                                "title": "Extracting training data from large language models.",
                                "link": "https://arxiv.org/pdf/2012.07805",
                                "abstract": "It has become common to publish large (billion parameter) language "
                                "models that have been trained on private datasets. This paper "
                                "demonstrates that in such settings, an adversary can perform a "
                                "training data extraction attack to recover individual training "
                                "examples by querying the language model. ...",
                            },
                            {
                                "title": "Assisting in Writing Wikipedia-like Articles From Scratch with Large "
                                "Language Models",
                                "link": "https://arxiv.org/pdf/2402.14207",
                                "abstract": "We study how to apply large language models to write grounded and "
                                "organized long-form articles from scratch, with comparable breadth and "
                                "depth to Wikipedia pages. This underexplored problem poses new "
                                "challenges at the pre-writing stage, including how to research the "
                                "topic and prepare an outline prior to writing.",
                            },
                        ],
                    }
                },
            ),
            (
                "The first paper is relevant while the second is not relevant. I will only add relevant papers to "
                "the library.",
                'ADD_PAPER_TO_LIBRARY(titles=["Extracting training data from large language models."], '
                'links=["https://arxiv.org/pdf/2012.07805"])',
                {
                    "library": [
                        {
                            "title": "Extracting training data from large language models.",
                            "link": "https://arxiv.org/pdf/2012.07805",
                            "notes": ["..."],
                        }
                    ]
                },
            ),
            (
                "...(omitted several steps where I search with relevant queries to get more papers)... "
                "Now there are 20 papers in the library. I can use them to draft the related works section.",
                'LIBRARY_TO_DRAFT(example="...")',
                {"related_works_editor": "..."},
            ),
            (
                "The draft overall looks good. I still need to polish it based on my teammate's suggestions.",
                'EDITOR_UPDATE(text="...")',
                {"related_works_editor": "..."},
            ),
        ]

    # Private actions
    def _search_arxiv(self, role: str, query: str):
        search_results = []

        if self.use_simulated_dataset:
            documents = self.paper_retriever.retrieve(query=query)
            for doc in documents:
                search_results.append(
                    {
                        "title": " ".join(
                            doc["title"].split()
                        ),  # Better handling of "\n"
                        "link": f"https://arxiv.org/pdf/{doc['id']}",
                        "abstract": doc["abstract"],
                    }
                )
        else:
            search = arxiv.Search(
                query=query,
                max_results=self.retrieve_top_k,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending,
            )
            results = self.paper_retriever.results(search)
            for r in results:
                search_results.append(
                    {
                        "title": " ".join(r.title.split()),  # Better handling of "\n"
                        "link": str(r).replace("abs", "pdf"),
                        "abstract": r.summary.replace("\n", " "),
                    }
                )

        self.search_window[role] = {"query": query, "results": search_results}

    # Shared actions
    def _add_paper_to_library(self, titles: str, links: str):
        titles_list = json.loads(titles)
        links_list = json.loads(links)

        def extract_notes(paper_title, paper_link):
            extracted_notes = self.extract_notes(paper_link=paper_link)
            return paper_title, paper_link, extracted_notes

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for title, link in zip(titles_list, links_list):
                if title in self.paper_library_titles:
                    raise ValueError(
                        f"Fail to add paper: {title} is already in the paper list"
                    )
                else:
                    futures.append(executor.submit(extract_notes, title, link))

            for future in as_completed(futures):
                title, link, notes = future.result()
                self.paper_library.append(
                    {
                        "title": title,
                        "link": link,
                        "notes": "\n".join([f"- {note}" for note in notes]),
                    }
                )
                self.paper_library_titles.add(title)

    def _drop_paper_from_library(self, title):
        self.paper_library = [
            paper for paper in self.paper_library if paper["title"] != title
        ]

        if title in self.paper_library_titles:
            self.paper_library_titles.remove(title)
        else:
            raise ValueError(
                f"Fail to drop {title}. Make sure this paper exists in the list and is spelled correctly"
            )

    def _library_to_draft(self, example: str):
        related_works = self.write_related_works_module(
            query=self.query,
            papers=self.paper_library,
            example=example,
        )
        self.related_works_editor.update_text(related_works)

    def _polish_draft_with_library(self, polishing_request: str):
        polished_related_works = self.polish_related_works_module(
            papers=self.paper_library,
            current_draft=self.related_works_editor.get_text(),
            polishing_request=polishing_request,
        )
        self.related_works_editor.update_text(polished_related_works)

    def _editor_update(self, text: str):
        self.related_works_editor.update_text(text)

    def close(self):
        pass

    def get_obs(self):
        return {
            "public": {
                "library": self.paper_library,
                "related_works_editor": self.related_works_editor.get_text(),
            },
            "private": {
                team_member: {
                    "search_window": self.search_window[team_member],
                }
                for team_member in self.team_members
            },
        }

    def obs_type(self) -> dict[str, ObservationTypes]:
        return {
            "library": ObservationTypes.PAPER_LIBRARY,
            "search_window": ObservationTypes.PAPER_SEARCH,
            "related_works_editor": ObservationTypes.TEXT_EDITOR,
        }

    def reset(
        self,
        options: dict[str, Any] | None = None,
    ):
        self.paper_library = []
        self.paper_library_titles = set()
        self.search_window = {
            team_member: {"query": "", "results": []}
            for team_member in self.team_members
        }

        # self.outline = ""
        self.related_works_editor.update_text("")

        obs = self.get_obs()
        return obs, {}

    def step(self, role: str, action: str):
        """Execute one timestep within the environment.

        Args:
            role (str): The team member executing the action
            action (str): The action to take, formatted as a string matching one of the action space patterns

        Returns:
            observation, reward, termination state, private, additional information
        """
        info = {}
        info["action_start_time"] = time.time()

        # Parse and validate action using parent class helper
        parsed_action, private, action_id, err_msg = self.parse_and_validate_action(
            role, action
        )
        if err_msg:
            return self.handle_action_error(err_msg, private)

        # Post-process parsed action parameters
        for k in parsed_action:
            parsed_action[k] = post_process_parsed_function_arg(parsed_action[k])

        info["action"] = action_id

        # Execute the action
        terminated = False
        reward = 0  # Set intermediate reward to 0 if the action is successful; otherwise, -1.
        info["action_error"] = None

        try:
            if info["action"] == LitSurveyActions.SEARCH_ARXIV:
                self._search_arxiv(role=role, query=parsed_action["query"])
            elif info["action"] == LitSurveyActions.ADD_PAPER_TO_LIBRARY:
                self._add_paper_to_library(
                    titles=parsed_action["titles"], links=parsed_action["links"]
                )
            elif info["action"] == LitSurveyActions.DROP_PAPER_FROM_LIBRARY:
                self._drop_paper_from_library(title=parsed_action["title"])
            elif info["action"] == LitSurveyActions.LIBRARY_TO_DRAFT:
                self._library_to_draft(example=parsed_action["example"])
            elif info["action"] == LitSurveyActions.POLISH_DRAFT_WITH_LIBRARY:
                self._polish_draft_with_library(
                    polishing_request=parsed_action["polishing_request"]
                )
            elif info["action"] == LitSurveyActions.EDITOR_UPDATE:
                self._editor_update(text=parsed_action["text"])
            elif info["action"] == LitSurveyActions.FINISH:
                terminated = True
        except Exception as e:
            err_msg = f"Error in executing the action: {action}. Error: {e}"
            return self.handle_action_error(err_msg, private)
        finally:
            info["action_end_time"] = time.time()

        # Get the observation
        obs = self.get_obs()

        return obs, reward, terminated, private, info

    @staticmethod
    def link_inline_citations(text: str, library: list[dict[str, str]]) -> str:
        """Link inline citations based on Markdown format."""
        citation_map = {
            str(i + 1): citation["link"] for i, citation in enumerate(library)
        }

        def replace_citation(match):
            citation_number = match.group(1)
            link = citation_map.get(citation_number, "")
            return f"[[{citation_number}]({link})]" if link else f"[{citation_number}]"

        linked_text = re.sub(r"\[(\d+)\]", replace_citation, text)
        return linked_text

    def evaluate_task_performance(self):
        performance = {
            "query": self.query,
            "pure_text": self.related_works_editor.get_text(),
            "paper_library": self.paper_library,
        }
        if (
            len(self.paper_library) == 0
            or len(self.related_works_editor.get_text().strip()) == 0
        ):
            performance["outcome"] = ""
            performance["task_completion"] = 0
            performance["performance_rating"] = 0
            return performance

        performance["outcome"] = self.link_inline_citations(
            performance["pure_text"], self.paper_library
        )
        performance["task_completion"] = 1

        if self.use_simulated_dataset:
            rubric = open(self.rubric_path).read()
            evaluation_prompt = rubric.format(
                topic=self.data_point["title"], related_works=performance["pure_text"]
            )
            output = self.evaluator_lm(
                prompt=evaluation_prompt,
                temperature=0,
                max_tokens=500,
            )[0].strip()
            if "the final score is 1" in output:
                performance["performance_rating"] = 1 / 5  # Normalize to [0, 1]
            elif "the final score is 2" in output:
                performance["performance_rating"] = 2 / 5
            elif "the final score is 3" in output:
                performance["performance_rating"] = 3 / 5
            elif "the final score is 4" in output:
                performance["performance_rating"] = 4 / 5
            elif "the final score is 5" in output:
                performance["performance_rating"] = 5 / 5
            else:
                performance["performance_rating"] = ""
            performance["evaluation_output"] = output

        return performance

    def __repr__(self):
        return f"LitSurveyEnv(use_simulated_dataset={self.use_simulated_dataset}, query={self.query})"
