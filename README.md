# Example OpenADR client using openLEADR

This is a sample project that shows how to use openLEADR. This client will connect to a VTN, attempt to register, and print any events it receives to the standard output. It also offers to provide two dummy reports to the VTN. A sample certificate is included that will sign outgoing messages.

## Installation

On Linux or macOS:

```
git clone https://github.com/openleadr/openleadr-example-ven
cd openleadr-ven
python -m venv python_env
./python_env/bin/pip install .
```

On Windows:

```
git clone https://github.com/openleadr/openleadr-example-ven
cd openleadr-ven
python -m venv python_env
python_env\Scripts\pip install .
```

## Configure and run

You can configure basic settings in `config.yml`.

You can run the client like this:

```
./python_env/bin/python -m openleadr_ven
```
