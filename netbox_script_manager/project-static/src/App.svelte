<script>
    import SvelteTable from "svelte-table";
    import { onMount } from "svelte";

    const capitalize = (s) => (s && s[0].toUpperCase() + s.slice(1)) || "";

    const BASE_URL = "/api/plugins/script-manager";
    const LOG_LINES_URL = `${BASE_URL}/script-log-lines/`;
    const SCRIPT_EXECUTIONS_URL = `${BASE_URL}/script-executions/`;

    // Easiest way to pass the ScriptResult id from the template to the Svelte app
    // when bundled as iife
    let result_id = document.script_manager.result_id;
    $: rows = [];
    let selection = {};

    // Mapping of log level to bootstrap color
    let levelColors = {
        debug: "text-bg-gray",
        info: "text.bg-cyan",
        success: "text-bg-green",
        warning: "text-bg-yellow",
        failure: "text-bg-red",
    };

    // Column definitions
    const columns = [
        {
            key: "timestamp",
            title: "Time",
            value: (v) => v.timestamp_formatted,
            sortable: true,
            class: "text-nowrap",
            headerClass: "min-width-120",
            parseHTML: true,
        },
        {
            key: "level",
            title: "Level",
            value: (v) => v.level,
            sortable: true,
            filterOptions: ["Debug", "Info", "Success", "Warning", "Failure"],
            filterValue: (v) => capitalize(v.level),
            renderValue: (v) => {
                let bgColor = levelColors[v.level.toLowerCase()];
                return `<span class="badge ${bgColor}">${capitalize(
                    v.level,
                )}</span>`;
            },
            parseHTML: true,
            filterPlaceholder: "All",
            headerClass: "min-width-70",
        },
        {
            key: "message",
            title: "Message",
            value: (v) => v.message_markdown,
            sortable: true,
            parseHTML: true,
            searchValue: (v) => v.message,
            class: "w-100",
            headerClass: "w-100",
            filterPlaceholder: "Search message",
        },
    ];

    onMount(() => {
        // If the script already has logs, we pre-load them from the template to speed up presentation
        if (document.script_manager.logs.length > 0) {
            rows = [...document.script_manager.logs];
        }
        lazyLoadRows();

        return () => {};
    });

    /**
     * Get the ScriptResult object from the API
     *
     * @param last_id The last ID fetched from the API
     */
    async function getScriptResult() {
        let url = `${SCRIPT_EXECUTIONS_URL}${result_id}`;

        const response = await fetch(url);
        const data = await response.json();

        return data;
    }

    async function lazyLoadRows() {
        let last_id = null;

        // If we already have rows, we start from the last one
        if (rows.length > 0) {
            last_id = rows[rows.length - 1].id;
        }

        while (true) {
            let scriptResult = await getScriptResult();

            last_id = await getScriptLogs(last_id);

            if (scriptResult.completed) {
                waitForArtifactTable();
                break;
            }

            await new Promise((r) => setTimeout(r, 1000));
        }
    }

    async function waitForArtifactTable() {
        await new Promise((r) => setTimeout(r, 2500));
        document.script_manager.script_completed = true;
    }

    async function getScriptLogs(last_id) {
        let url = `${LOG_LINES_URL}?script_execution=${result_id}`;

        if (last_id) {
            url = `${url}&id__gt=${last_id}`;
        }

        while (true) {
            const response = await fetch(url);
            const data = await response.json();

            rows = [...rows, ...data.results];

            if (data.next) {
                url = data.next;
            } else {
                break;
            }
        }

        if (rows.length > 0) {
            return rows[rows.length - 1].id;
        } else {
            return null;
        }
    }
</script>

<SvelteTable
    {columns}
    {rows}
    bind:filterSelections={selection}
    classNameTable={["table table-hover"]}
    classNameInput={["ts-control"]}
/>
