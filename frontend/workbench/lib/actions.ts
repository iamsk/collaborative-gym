type ActionParams = Record<string, string | number | undefined>;

abstract class Action {
  abstract regexPattern: RegExp;
  abstract machineReadableIdentifier: string;
  abstract humanReadableName: string;
  abstract humanReadableDescription: string;

  params: ActionParams;

  constructor(params: ActionParams = {}) {
    this.params = params;
  }

  validateActionString(actionString: string): boolean {
    return this.regexPattern.test(actionString);
  }

  abstract formatActionString(): string;
}

export class EditorUpdateAction extends Action {
  regexPattern = /^EDITOR_UPDATE\(text=(.*)\)$/;
  machineReadableIdentifier = 'EDITOR_UPDATE';
  humanReadableName = 'Update the travel plan editor';
  humanReadableDescription =
    'Update the travel plan editor with the provided text.';

  constructor(text: string) {
    super({ text });
  }

  formatActionString(): string {
    return `EDITOR_UPDATE(text=${this.params.text})`;
  }
}

export class SendTeammateMessageAction extends Action {
  regexPattern = /^SEND_TEAMMATE_MESSAGE\(message=(.*)\)$/;
  machineReadableIdentifier = 'SEND_TEAMMATE_MESSAGE';
  humanReadableName = 'Send a message to your teammate(s)';
  humanReadableDescription =
    'Send a message to your teammate(s) to provide information, ask for feedback, allocate tasks, etc. This action is useful for collaboration.';

  constructor(message: string) {
    super({ message });
  }

  formatActionString(): string {
    return `SEND_TEAMMATE_MESSAGE(message=${this.params.message})`;
  }
}

export class FinishAction extends Action {
  regexPattern = /^FINISH\(\)$/;
  machineReadableIdentifier = 'FINISH';
  humanReadableName = 'Finish the travel planning task';
  humanReadableDescription = 'Finish the travel planning task.';

  formatActionString(): string {
    return 'FINISH()';
  }
}

export class AcceptConfirmationAction extends Action {
  regexPattern = /^ACCEPT_CONFIRMATION\(request_id=(.*)\)$/;
  machineReadableIdentifier = 'ACCEPT_CONFIRMATION';
  humanReadableName = 'Accept the confirmation';
  humanReadableDescription =
    'Accept the confirmation based on the provided request ID.';

  constructor(requestId: string) {
    super({ requestId });
  }

  formatActionString(): string {
    return `ACCEPT_CONFIRMATION(request_id=${this.params.requestId})`;
  }
}

export class RejectConfirmationAction extends Action {
  regexPattern = /^REJECT_CONFIRMATION\(request_id=(.*)\)$/;
  machineReadableIdentifier = 'REJECT_CONFIRMATION';
  humanReadableName = 'Reject the confirmation';
  humanReadableDescription =
    'Reject the confirmation based on the provided request ID.';

  constructor(requestId: string) {
    super({ requestId });
  }

  formatActionString(): string {
    return `REJECT_CONFIRMATION(request_id=${this.params.requestId})`;
  }
}

export class PutAgentAsleepAction extends Action {
  regexPattern = /^PUT_AGENT_ASLEEP\(\)$/;
  machineReadableIdentifier = 'PUT_AGENT_ASLEEP';
  humanReadableName = 'Put the agent to sleep';
  humanReadableDescription =
    'Put the agent to sleep, preventing it from taking actions.';

  formatActionString(): string {
    return 'PUT_AGENT_ASLEEP()';
  }
}

export class WakeAgentUpAction extends Action {
  regexPattern = /^WAKE_AGENT_UP\(\)$/;
  machineReadableIdentifier = 'WAKE_AGENT_UP';
  humanReadableName = 'Wake the agent up';
  humanReadableDescription =
    'Wake the agent up, allowing it to take actions.';

  formatActionString(): string {
    return 'WAKE_AGENT_UP()';
  }
}

export class BusinessSearchAction extends Action {
  regexPattern = /^BUSINESS_SEARCH\(term=(.*), location=(.*), limit=(.*)\)$/;
  machineReadableIdentifier = 'CoTravelPlanningActions.BUSINESS_SEARCH';
  humanReadableName =
    'Find businesses (restaurants, hotels, etc.) on Google Places';
  humanReadableDescription =
    'Find businesses (restaurants, hotels, etc.) on Google Places based on the provided term, location, and limit.';

  constructor(term: string, location: string, limit: number) {
    super({ term, location, limit });
  }

  formatActionString(): string {
    const { term, location, limit } = this.params;
    return `BUSINESS_SEARCH(term=${term}, location=${location}, limit=${limit})`;
  }
}

export class InternetSearchAction extends Action {
  regexPattern = /^INTERNET_SEARCH\(query=(.*)\)$/;
  machineReadableIdentifier = 'CoTravelPlanningActions.INTERNET_SEARCH';
  humanReadableName = 'Search the Internet';
  humanReadableDescription =
    'Search the Internet based on the provided query.';

  constructor(query: string) {
    super({ query });
  }

  formatActionString(): string {
    return `INTERNET_SEARCH(query=${this.params.query})`;
  }
}

export class DistanceMatrixAction extends Action {
  regexPattern = /^DISTANCE_MATRIX\(origins=(.*), destinations=(.*), mode=(.*)\)$/;
  machineReadableIdentifier = 'CoTravelPlanningActions.DISTANCE_MATRIX';
  humanReadableName = 'Get distance matrix from Google Maps';
  humanReadableDescription =
    'Get distance matrix from Google Maps based on the provided origins, destinations, and mode.';

  constructor(origins: string[], destinations: string[], mode: string) {
    const originsStr =
      '[' + origins.map((origin) => `"${origin}"`).join(', ') + ']';
    const destinationsStr =
      '[' + destinations.map((destination) => `"${destination}"`).join(', ') + ']';
    super({ origins: originsStr, destinations: destinationsStr, mode });
  }

  formatActionString(): string {
    const { origins, destinations, mode } = this.params;
    return `DISTANCE_MATRIX(origins=${origins}, destinations=${destinations}, mode=${mode})`;
  }
}

export class ExecuteJupyterCellAction extends Action {
  regexPattern = /^EXECUTE_JUPYTER_CELL\(code=(.*)\)$/;
  machineReadableIdentifier = 'CoAnalysisActions.EXECUTE_JUPYTER_CELL';
  humanReadableName = 'Execute code in Jupyter cell';
  humanReadableDescription =
    'Execute the given Python code or Jupyter magic command in a Jupyter cell based on the current Jupyter execution context. Avoid printing long outputs, as they will exceed the character limit. For file saving, only access the Docker volume container directory.';

  constructor(code: string) {
    super({ code });
  }

  formatActionString(): string {
    return `EXECUTE_JUPYTER_CELL(code=${this.params.code})`;
  }
}

export class AddPaperToLibraryAction extends Action {
  regexPattern = /^ADD_PAPER_TO_LIBRARY\(titles=(.*), links=(.*)\)$/;
  machineReadableIdentifier = 'LitSurveyActions.ADD_PAPER_TO_LIBRARY';
  humanReadableName = 'Add paper(s) to the shared library';
  humanReadableDescription =
    'Add paper(s) to the shared library. Ensure titles and links match in order. The library will automatically extract notes.';

  constructor(titles: string[], links: string[]) {
    const titlesStr =
      '[' + titles.map((title) => `"${title}"`).join(', ') + ']';
    const linksStr =
      '[' + links.map((link) => `"${link}"`).join(', ') + ']';
    super({ titles: titlesStr, links: linksStr });
  }

  formatActionString(): string {
    const { titles, links } = this.params;
    return `ADD_PAPER_TO_LIBRARY(titles=${titles}, links=${links})`;
  }
}

export class DropPaperFromLibraryAction extends Action {
  regexPattern = /^DROP_PAPER_FROM_LIBRARY\(title=(.*)\)$/;
  machineReadableIdentifier = 'LitSurveyActions.DROP_PAPER_FROM_LIBRARY';
  humanReadableName =
    'Drop a recommended paper from the shared paper list';
  humanReadableDescription =
    'Drop a recommended paper from the shared library based on the title.';

  constructor(title: string) {
    super({ title });
  }

  formatActionString(): string {
    return `DROP_PAPER_FROM_LIBRARY(title=${this.params.title})`;
  }
}

export class LibraryToDraftAction extends Action {
  regexPattern = /^LIBRARY_TO_DRAFT\(example=(.*)\)$/;
  machineReadableIdentifier = 'LitSurveyActions.LIBRARY_TO_DRAFT';
  humanReadableName =
    'Update the editor with the related works draft based on the papers in the library';
  humanReadableDescription =
    'Create a related works draft based on the topic and collected papers, and overwrite current editor content if `example` is provided.';

  constructor(example: string) {
    super({ example });
  }

  formatActionString(): string {
    return `LIBRARY_TO_DRAFT(example=${this.params.example})`;
  }
}

export class SearchArxivAction extends Action {
  regexPattern = /^SEARCH_ARXIV\(query=(.*)\)$/;
  machineReadableIdentifier = 'LitSurveyActions.SEARCH_ARXIV';
  humanReadableName = 'Search arXiv API given a query';
  humanReadableDescription =
    "Searches arXiv API for the given query, returning a list with 'url', 'pdf', and metadata, which will be stored in the search window.";

  constructor(query: string) {
    super({ query });
  }

  formatActionString(): string {
    return `SEARCH_ARXIV(query=${this.params.query})`;
  }
}
