# Analyze numerical issues in linear programs

This tool helps analyze numerical issues in a linear programming
model (LP and MIP). I started developing it will doing research for the [REAM Research Lab](https://patyhidalgo.github.io/)
on the [SWITCH](http://switch-model.org/) Power System Planning
Model.


## Usage

1. `pip install lp-analyzer`
2. `lp-analyzer <path_to_mps_model_file>`
3. The generated output file gives
insight into the numerical properties of the model. For example, it outputs the range of the coefficients
of each constraint type and each variable type.

See instructions below to learn how to generate a [`.mps` file](https://en.wikipedia.org/wiki/MPS_(format)) with Pyomo, Switch or Gurobi.

## Detailed guide

### What are numerical issues in linear programming?

[Linear programming](https://en.wikipedia.org/wiki/Linear_programming) allows us to find optimal solutions
to problems by defining problems as a set of linear equations.

Today, there exists numerical solvers that can read millions
of these equations and find the optimal solution automatically. 
For example, [Gurobi](https://www.gurobi.com/) is one of these solvers.

These millions of equations have numerical coefficients. When these
coefficients are too large or too small in magnitude (e.g. 10<sup>10</sup>
or 10<sup>-10</sup>), solvers like Gurobi struggle to find
the optimal solution. We say that we're encountering numerical
issues. This is because such large or small
values are challenging to store on a floating-point computer
(see [here](https://www.itu.dk/~sestoft/bachelor/IEEE754_article.pdf) for more info).

One solution to this problem is 'scaling' the equations.
Basically if all the numbers are too big we can scale them down
without affecting our results.

### What does this tool do?

To scale our model, we need to know how big or small or numbers are
(to know how much we should scale them by). This tool
helps you figure that out! Analyzing the equations by hand
is challenging since models can get extremely large. This
tool automatically analyzes a linear programming model
and returns the range of different coefficients
 to help you determine which coefficients need scaling.

### How to use this tool?

#### Install it

Simply run `pip install lp-analyzer`.

If you want to install from the source code, clone the repository to download the code
and run within the directory `pip install .`.

#### Run it on a `.mps` file

For now this tool only reads [`.mps` files](https://en.wikipedia.org/wiki/MPS_(format)). This
file type stores a linear program model.

Once you have your `.mps` file simply run:

`lp_analyzer path/to/file.mps`

The relevant ranges will be automatically be saved to a file! 
To change the output file use `-o output.txt`.

#### Using with Pyomo

If you're trying to use
this tool with a Pyomo model you'll first need to generate
a `.lp` file then a `.mps` file. 

First solve the model with `keepfiles=True, symbolic_solver_labels=True`. For example,

```
results = solver.solve(model, tee=True, keepfiles=True, symbolic_solver_labels=True)
```

This will save an `.lp` file to a temporary directory (as listed in the console output).


Once you have your `.lp` file, you can use the Gurobi
prompt to convert it to an `.mps` file.

Open the Gurobi prompt (normally just run `gurobi`),
then run the following commands. This will create a
`model_file.mps` file which you can use with this tool (see above).

```
gurobi> m = read("model_file.lp")
...
gurobi> m = m.presolve()
...
gurobi> m.write("model_file.mps")
```
The `presolve()` step is optional, but will remove
unnecessary equations making your analysis more relevant.
You can read more about `presolve()` [here](https://www.gurobi.com/documentation/9.1/refman/presolve2.html).

#### Using with SWITCH

[SWITCH](https://github.com/switch-model/switch) 
is a platform for planning high-renewable power systems
that uses linear programming.

The steps to using this library with SWITCH are nearly identical to that of using it with Pyomo.
The only difference is you can use the following command to generate the `.lp` file.

`switch solve --solver gurobi -v --keepfiles --tempdir temp --symbolic-solver-labels`

This will save the `.lp` file to the `temp` folder. 
To learn more about what each flag does run `switch solve -h`.
