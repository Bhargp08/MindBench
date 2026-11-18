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
- **Mock mode** (default): `createSaver({ mode: "mock" })` keeps a JSON copy and the shell downloads it; nothing is sent anywhere.
- **Production mode** (`VITE_MINDBENCH_MODE=production`, `VITE_DATAPIPE_EXPERIMENT_ID=<12-char ID>`): `createSaver` returns the DataPipe extension (`buildPipeExtension`), registered in `initJsPsych`. File name `<code>_session<N>.json`; format JSON; streaming on. Metadata, questionnaire, participant code and session number are attached to every trial row with `jsPsych.data.addProperties` after the questionnaire, because the extension uploads jsPsych's own data.
- **`?simulate` URL flag:** disables the extension (`enabled: false`), so test runs never write to the dataset. Always use it when trying a production build with a real ID.
- The extension logs a warning at start that the filename function threw (the participant code is not known yet) and calls it again at the end, as its README documents.
- **Caution:** loading a production build **without** `?simulate` contacts DataPipe immediately (session start), even before any trial.
- Verified in a browser with a fake experiment ID and `?simulate`: no DataPipe requests, session runs to the end. A real upload has **not** been tested; that needs a DataPipe experiment ID from Bharg (external action) and should be tried first with a throwaway experiment.
