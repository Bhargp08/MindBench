# DataPipe integration (verified Nov 17, 2026)

**Answer to "plugin or extension?":** both exist on npm, but DataPipe's own getting-started page (https://pipe.jspsych.org/getting-started) recommends the **extension**.

| Package | Version | Notes |
|---|---|---|
| `@jspsych/extension-pipe` | 0.2.0 (peer `jspsych >=8.0.0`) | **Recommended.** Registered in `initJsPsych({ extensions: [...] })`; no save trial. Stages each trial as it finishes, submits the full dataset at the end, also after `abortExperiment()`. |
| `@jspsych-contrib/plugin-pipe` | 0.6.0 | Older plugin (a save trial in the timeline). Its README still describes routing to an OSF component, which no longer fits (DataPipe stops writing to OSF after Nov 16, 2026). The extension's README says to delete the plugin's save trial when migrating, because using both submits twice and counts as a failed save. |

Sources read: the published `@jspsych/extension-pipe` 0.2.0 README and type definitions and the `@jspsych-contrib/plugin-pipe` 0.6.0 README (from the npm tarballs), plus the DataPipe getting-started page. The `/sending-data` docs URL returned 404, so the extension README is the API reference used.

## Extension API (from the 0.2.0 README and `index.d.ts`)
```js
initJsPsych({
  extensions: [{
    type: jsPsychExtensionPipe,               // global in the browser build; default export when bundled [confirm on install]
    params: {
      experiment_id: "<12-char ID>",          // required; not a secret
      filename: () => `${code}.json`,         // required, unique per file; function evaluated at start
      format: "csv" | "json",                 // default csv; ignored if data_string is given
      data_string: () => string,              // optional custom payload
      stream: true,                           // stage each trial (recoverable as .partial.json)
      enabled: true,                          // MUST be false for jsPsych.simulate()
      wait_message, done_message, on_save: (result) => {}, base_url
    }
  }]
});
```
Notes: the extension wraps `on_data_update` and `on_finish`; failed saves are reported only through `on_save` (`result.ok`); keep requests under DataPipe's 32 MB limit; storage backends are Google Drive, Dataverse and Zenodo (D1: Google Drive).

## Status in this repo
- MB-06 ships **mock mode only** (`createSaver({ mode: "mock" })`, with a JSON download). `mode: "production"` throws until the production adapter is added.
- Production adapter (separate, tested step): build the extension config from the validated `experimentId`, use `enabled: false` when simulating, report failures through `on_save`, use a participant-code-based unique filename. Not yet written; install of `@jspsych/extension-pipe` and the exact import form still to be confirmed.
- DataPipe dashboard setup (creating the experiment, choosing Google Drive) is an external action for Bharg.
