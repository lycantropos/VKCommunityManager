## Installing the application on Ubuntu 14.04
Everywhere onwards it is assumed that `vk-community-manager/` is an installation directory where
`vk-community-manager/` is a conventional sign for the full path to installation directory.

### Installing required environment

Install relational database management system `MySQL`
and `libmysqlclient-dev` package (`mysqlclient` package requirement):

```bash
sudo apt-get install -y mysql-server
sudo apt-get install -y libmysqlclient-dev
```

Add repository and install `Python 3.5` with `python3.5-dev` package
(`mysqlclient` and `numpy` packages' requirement):

```bash
sudo add-apt-repository ppa:fkrull/deadsnakes
sudo apt-get update
sudo apt-get install -y python3.5 python3.5-dev
```

Install `Python 3.5` package manager - `pip` and upgrade it:

```bash
sudo apt-get install -y python3-pip
sudo python3.5 -m pip install --upgrade pip
```

Install version control system - `git`:

```bash
sudo apt-get install -y git
```

### Installing the application
Create and switch to the application directory:

```bash
mkdir vk-community-manager
cd vk-community-manager
```

Initialize the application:
```bash
git clone https://github.com/lycantropos/VKCommunityManager.git
```

**Important**

In the following instructions it is assumed that commands are executed from `vk-community-manager/` directory.

#### Setting up the configuration files

Make a copy of developer configuration files:
```bash
cd configurations
cp empty_configuration.conf configuration.conf
```

Make changes in configuration files `configuration.conf`.
The settings are read once when the application starts.
After updating settings, you must restart the application.

### Building the application

Update/install required `Python 3.5` packages:

```bash
sudo python3.5 -m pip install --upgrade -r requirements.txt
```
