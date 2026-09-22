---
title: HowTo Markdown
date: 2020-12-10
---

## Header management

``` md
<!--- Use this syntax to create a Header level 1 --->
# Heading 1

<!--- Use this syntax to create a Header level 2 --->
## Heading 2

<!--- Use this syntax to create a Header level 3 --->
### Heading 3
```

## Common text

``` md
<!--- Use this syntax to create a common text. --->
<!--- Please note that you need a blank line between paragraphes --->
Common text
<!--- Use this syntax to create an emphasized text --->
*Emphasized text*
<!--- Use this syntax to create a strikethrough text --->
~~Strikethrough text~~
<!--- Use this syntax to create a strong text --->
**Strong text**
<!--- Use this syntax to create a strong emphasized text --->
***Strong emphasized text***
<!--- Use this syntax to create a strong emphasized text --->
***Strong emphasized text***
<!--- Horizontal line --->
- - - -
```

## Links

### Internal links

If you are like this:

``` shell
.
├─ README.md
├─ foo
│  ├─ README.md
│  ├─ one.md
│  └─ two.md
└─ bar
   ├─ README.md
   ├─ three.md
   └─ four.md
```

And providing you are in foo/one.md:

``` md
[Home](/) <!-- Sends the user to the root README.md -->
[foo](/foo/) <!-- Sends the user to index.html of directory foo -->
[foo heading](./#heading) <!-- Anchors user to a heading in the foo README file -->
[bar - three](../bar/three.md) <!-- You can append .md (recommended) -->
[bar - four](../bar/four.html) <!-- Or you can append .html -->
```

### External links

``` md
<!--- Use this syntax to create an external link. --->
<!--- Replace the Named link with the one that need to be displayed. --->
[Named Link](http://www.google.fr/)
```

## Images

``` md
<!--- This is how to add an image in the page --->
![picture alt](http://www.cdisc.org/sdtm/sdtmig3_3.png "Title is optional")
```

## Lists

``` md
<!--- Bullet point list --->
* Bullet list
    * Nested bullet
        * Sub-nested bullet etc
    * Bullet list item 2

<!--- Numbered list --->
1. A numbered list
    1. A nested numbered list
    2. Which is numbered
2. Which is numbered

<!--- Foldable text --->
<details>
    <summary>Title 1</summary>
    <p>Content 1 Content 1 Content 1 Content 1 Content 1</p>
</details>
```

## GitHub-Style Tables

``` md
<!--- Solution to add tasks --->
| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |
```

## Custom Containers

Example:
::: danger
This is a dangerous warning
:::

``` md
<!--- Solution to have some Default Title --->
::: tip
This is a tip
:::

::: warning
This is a warning
:::

::: danger
This is a dangerous warning
:::

::: details
This is a details block, which does not work in IE / Edge
:::

<!--- Customer Title --->
::: danger STOP
Danger zone, do not proceed
:::
```

## Tasks

``` md
<!--- Solution to add tasks --->
- [ ] An uncompleted task
- [x] A completed task
```

## Bloquotes

> It is possible to have some bloquotes text

``` md
<!--- Bloquotes with different level --->
> Blockquote
    >> Nested Blockquote
```