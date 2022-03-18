# Keithley CSV Importer

This script takes data in the format Keithley stores it and converts it to the format used by the data processing script.

There are 2 parts to using this: logging during the experiment, and copying data from the Keithley S4200 machine.

**Warning:** Currently only supports 2 probe data

# Logging During the Experiment(s)

All the Runs are stored in a `.yml` file in chronological order, consisting of the following
- The name of the run
- The cell measured
- Any configuration parameters (ramp rate, Icc, etc)

## Definitions

### Position

This is the syntax for specifying a particular cell

```yaml
wafer: <wafer name>
grid: <grid>
subgrid: <subgrid>
cell: <cell>
```

Example, the cell `(wafer2,0,0,-1,-1,3,4)`

```yaml
wafer: wafer2
grid: 0,0
subgrid: -1,-1
cell: 3,4
```

**Note:** Don't use tuple syntax like in Python

### Time

This is for saving the experiment time. You probably won't need it since it may be determined from the data.

```yaml
time: <iso timestamp>
```

Example,

```yaml
time: 2022-03-18 00:34:05
```

## Run Formats

### Set/Form

```yaml
Set <run #>:
    op: <set/form>
    time: <time>
    position: [Position]
    icc: <compliance current with units>
    rr: <ramp rate in V/s>
    start: <start voltage>
    end: <end voltage>
    step: <the step size in Keithley>
    comment: <comment to be included>
```

Example

```yaml
Set 125:
    op: form
    time: 2022-03-17 14:57:05
    position:
        wafer: wafer2
        grid: 0,0
        subgrid: -1,-1
        cell: 0,2
    icc: 20uA
    rr: 1
    start: 0
    end: 5
    step: 0.05
    comment: Nano-amps range, probably not connected
```

### Reset

Very similar to set/form, except you don't need to provide the `op` field.

```yaml
Reset <run #>:
    time: <time>
    position: [Position]
    icc: <compliance current with units>
    rr: <ramp rate in V/s>
    start: <start voltage>
    end: <end voltage>
    step: <the step size in Keithley>
    comment: <comment to be included>
```

Example

```yaml
Reset 138:
    time: 2022-03-17 15:15:00
    position:
        wafer: wafer2
        grid: 0,1
        subgrid: -1,-1
        cell: 1,0
    icc: 6mA
    rr: 1
    start: 0
    end: -3
    step: -0.025
    comment: Did not reset
```

### Observe

```yaml
Observe <run #>:
    time: <time>
    position: [Position]
    icc: <compliance current with units>
    bias: <voltage bias of copper in V>
    comment: <comment to be included>
```

Example,

```yaml
Observe 184:
    time: 2022-03-17 15:18:05
    position:
        wafer: wafer2
        grid: 0,1
        subgrid: -1,-1
        cell: 1,0
    icc: 20uA
    bias: 0.1
    comment: Reset
```

### Efficient Logging

To make it easier to log things, redundant information may be omitted.
- `time` is never required, since it is in the Keithley data
- `start` and `end` are determined from data, but it may be helpful to include them as experimental notes
- In `Observe` runs, the state of the cell is estimated from the data
- Parameters that don't change from test to test (of the same type) may be omitted
- The cell `position` is only needed for the first test on that cell

Here are some examples to illustate these rules

```yaml
# need to include everything since this is the first run

Set 125:
    op: form
    position:
        wafer: wafer2
        grid: 0,0
        subgrid: -1,-1
        cell: 0,2
    icc: 20uA
    rr: 1
    step: 0.05
    comment: Nano-amps range, probably not connected


# always need op in set, this is not saved
# position, icc, rr, and step carried over

Set 126:
    op: form
    comment: Formed at 1.25 V


# provide position since the cell was changed
# other set parameters carried over

Set 127:
    op: form
    position:
        wafer: wafer2
        grid: 0,0
        subgrid: -1,-1
        cell: 0,3
    comment: No forming

...

# we're still at (wafer2,0,0,-1,-1,0,3)

# position inherited between runs of different types

Observe 183:
    icc: 20uA
    comment: Set


# position inherited, but need to include other
# parameters since this is the first Reset

Reset 138:
    icc: 6mA
    rr: 1
    start: 0
    end: -3
    step: -0.025
    comment: Did not reset


# provide icc and ending voltage since we changed them
# but everything else stays the same

Reset 139:
    icc: 8mA
    end: -4
    comment: Did not reset


# everything carried over

Reset 140:
    comment: Did reset
```

# Importing Data from Keithley

This script expects the data to be in the following structure

```
./
    Observe/
        Run116/
        Run117/
        ...
        <other observe run directories taken from keithley>
    Reset/
        Run189/
        Run190/
        ...
    Set/
        ...
    
    experiment_log.yml
```

## Steps to import Keithley data

For the purpose of this guide, assume we have a directory `D:\data` where we wish to store our files **which is on a USB device plugged into the machine**.

1. Make folders `data/Observe`, `data/Reset` and `data/Set` to hold the runs of each type

2. Navigate into our project directory and to the folder containing our task data, `C:\s4200\kiuser\Projects\MDE-Micron2021\tests\History`

    Inside there will be folders `Set#1`, `Reset#1` and `Observe#1`. These correspond to the folders we made in Step 1.

3. To copy over the Set data, copy the necessary folders in `C:\...\History\Set#1\Site@1\` to `data\Set`. Repeat for Reset and Observe.

    At this point you could unplug your USB device.

4. Run the script from the `data` directory

    ```bash
    $ cd data
    $ ls
    Observe Reset Set log.yml
    $ python /path/to/keithley_import.py log.yml [output_dir]
    ```

    After running, your directory might look something like this
    
    ```bash
    $ tree
    ├── Set
    │   ├── HistorySelRunRecords.txt
    │   ├── Run125
    │   │   ├── data@1[125].xls
    │   │   ├── dataConfig@1[125].kgs
    │   │   ├── run.xml
    │   │   ├── testConfig[125].kta
    │   │   └── testConfig[125].ktp
    │   ├── ...
    ├── Reset
    │   ├── ...
    ├── Observe
    │   ├── ...
    ├── output_dir
    │   ├── (wafer2,0,0,-1,-1,0,2)_220317145705_form_0_5_1_20uA.csv
    │   ├── (wafer2,0,0,-1,-1,0,2)_220317145756_form_0_5_1_20uA.csv
    │   ├── (wafer2,0,0,-1,-1,0,3)_220317150107_form_0_5_1_20uA.csv
    │   ├── ...
    ├── log.yml
    ```

    **Note:** If you encounter this warning
    ```
    WARNING *** file size (20650) not 512 + multiple of sector size (512)
    WARNING *** OLE2 inconsistency: SSCS size is 0 but SSAT size is non-zero
    ```
    Don't worry about it, the data is fine, the excel file library is freaking out somewhere.