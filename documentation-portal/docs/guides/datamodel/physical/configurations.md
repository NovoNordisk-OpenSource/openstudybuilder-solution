---
title: Configurations Data Model
date: 2021-08-06
---


## This page is a work in progress.

```
A template parameter represents a group of values that fit into a position within a template.
These groups contain 'template parameter values', strings that can be filled in to specify objectives, endpoints and timeframes.
A wide variety of template parameters values exist, with different properties. Template parameters can also be created from Control terminology.
An example template parameter is [Compound], with value [Metformin].




The image below shows the part of the physical model relating to template parameters.
![Neo4j Model for Study Versioning](/Data-Model-Documentation/img/template-parameter-model.png)

# Versioning
Like library objects, template parameters are also versioned. 


# Combining Template Parameters with Conjunctions
# Complex Template Parameters Values
The application supports the use of complex template parameters value: a single value that is made up of other template parameters.
A TimePoint is an example of such a parameter value - it uses X, Y, and Z. 
```

