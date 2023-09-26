<script>
    import SvelteTable from "svelte-table";
    import { onMount } from "svelte";

    const capitalize = (s) => (s && s[0].toUpperCase() + s.slice(1)) || "";

    const LOG_LINES_URL = "/api/plugins/script-manager/script-log-lines/";
    const SCRIPT_EXECUTIONS_URL =
        "/api/plugins/script-manager/script-executions/";

    // Easiest way to pass the ScriptResult id from the template to the Svelte app
    // when bundled as iife
    let result_id = document.netbox_script_manager.result_id;
    $: rows = [];
    let selection = {};

    // Mapping of log level to bootstrap color
    let levelColors = {
        debug: "bg-gray",
        info: "bg-cyan",
        success: "bg-green",
        warning: "bg-yellow",
        failure: "bg-red",
    };

    // Column definitions
    const columns = [
        {
            key: "timestamp",
            title: "Time",
            value: (v) => v.timestamp_formatted,
            sortable: true,
            class: "text-nowrap",
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
                    v.level
                )}</span>`;
            },
            parseHTML: true,
            filterPlaceholder: "All",
        },
        {
            key: "message",
            title: "Message",
            value: (v) => v.message_markdown,
            sortable: true,
            parseHTML: true,
            searchValue: (v) => v.message,
            class: "w-100",
            filterPlaceholder: "Search message",
        },
    ];

    onMount(() => {
        lazyLoadRows();

        return () => {};
    });

    async function getScriptResult(last_id) {
        let url = `${SCRIPT_EXECUTIONS_URL}${result_id}`;

        const response = await fetch(url);
        const data = await response.json();

        return data;
    }

    async function lazyLoadRows() {
        let last_id = null;

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
        document.netbox_script_manager.script_completed = true;
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

    /*
    function addRows() {
        let random_int = Math.floor(Math.random() * 100);
        // random String
        let random_string = Math.random().toString(36).substring(7);
        // another random string
        let random_string2 = Math.random().toString(36).substring(7);

        rows = [
            ...rows,
            {
                id: random_int,
                first_name: random_string,
                last_name: random_string2,
                pet: "woof",
            },
        ];
        console.log(rows);
    }
    */
</script>

<SvelteTable
    {columns}
    {rows}
    bind:filterSelections={selection}
    classNameTable={["table table-hover"]}
/>
