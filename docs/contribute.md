This is probably the most important page of the website. As a community, we need your contribution to grow!

There are many ways by which you can contribute to the growth of the *openhdemg* project, and all of them are equally important.

If you want to become part of the [team](about-us.md#meet-the-developers), read through the next sections to understand which ways of contribution fit better with your skills and expertise. For any question, or to begin the collaboration, [contact us](contacts.md) through your favorite channel.

## Contribution categories

:fontawesome-solid-microchip: &nbsp; Code development

This category is for individuals who want to contribute to the openhdemg project by writing code. As a developer, you can help enhance the framework's functionality, improve existing features, fix bugs, and implement new algorithms and analysis techniques. Your contributions will directly impact the usability and effectiveness of *openhdemg*. For details, read the specific section [Guidelines for code developers](#general-guidelines-for-code-developers).


:fontawesome-solid-brain: &nbsp; Knowledge sharing

In the knowledge sharing category, we invite individuals with specialised expertise to contribute their valuable insights and knowledge to the *openhdemg* project. By sharing your expertise, you can help others in the community gain a deeper understanding of advanced analysis techniques, coding practices, and best practices in the field of HD-EMG. Your contribution will empower others to make the most out of *openhdemg* and accelerate the progress of HD-EMG research. Knowledge sharing is crucial for the growth and advancement of the *openhdemg* community.

:fontawesome-solid-file-code: &nbsp; Code sharing

The code sharing category is dedicated to individuals who have developed their own algorithms in Python or other languages, such as MATLAB, and want to contribute them to the *openhdemg* community. Your contribution can range from implementing new analysis techniques, data processing algorithms, or innovative visualization methods. We welcome you to share your code and contribute to the collective knowledge of the project.

:octicons-codescan-checkmark-24: &nbsp; Accuracy check

Ensuring the accuracy and reliability of the *openhdemg* framework is paramount. In this category, you can contribute by thoroughly testing and verifying the results of the framework's analysis algorithms and functionalities and providing feedback on potential improvements or issues. In this way, you can help enhance the accuracy and validity of *openhdemg's* results and increase the credibility of the entire *openhdemg* project.

:fontawesome-solid-bullhorn: &nbsp; Promotion and advertising

In order to grow our community, it is essential to increase our visibility and reach. Promotion and advertising play a crucial role in spreading the word about the *openhdemg* project and attracting new contributors. By actively engaging in promotion and advertising efforts, you can help us reach a wider audience and encourage more individuals to join our community. There are various ways you can contribute to promotion and advertising:

1. Social Media: Help us promote *openhdemg* on social media platforms by sharing project updates, success stories, and relevant content. Use hashtags and tag relevant individuals or organizations to increase visibility.
2. Blogging and Content Creation: Write blog posts, articles, or tutorials about *openhdemg* and its benefits. Share your experiences, insights, and use cases to inspire others and encourage them to get involved.
3. Outreach and Collaboration: Connect with related communities, organizations, or academic institutions to collaborate on joint projects, guest blog posts, or events. By expanding our network, we can amplify our message and reach new audiences.
4. Presentations and Workshops: Offer presentations or workshops at conferences, seminars, or webinars to showcase the capabilities of *openhdemg*. Demonstrate its potential applications and engage with the audience to generate interest and curiosity.
5. Documentation and Case Studies: Contribute to the development of comprehensive documentation and case studies that highlight the value and impact of *openhdemg*. These resources will serve as references for researchers in the field.

## Open Call for Contributions

We welcome all enthusiastic individuals who wish to contribute to the *openhdemg* project but do not find an appropriate category for their ideas. If you have unique insights, suggestions, or contributions that can benefit the project, we encourage you to share them with us. Your diverse perspectives and ideas can drive innovation and shape the future of *openhdemg*. Together, we are a vibrant community dedicated to advancing the field. Join us and make a difference in the *openhdemg* project.

## General guidelines for code developers

By following these guidelines, you can ensure that your code contributions align with the project's standards and promote a smooth collaborative development process.

1. Familiarize Yourself with the Project: Take the time to understand the *openhdemg* framework, its goals, and its existing codebase. Explore the documentation, tutorials, and code repositories to gain insights into the project's structure, coding conventions, and design principles.
2. Select an Area of Contribution: Identify an area within *openhdemg* where you can make a meaningful impact. It could be enhancing existing features, fixing bugs, implementing new algorithms, or improving the overall functionality and performance of the framework.
3. Follow Coding Best Practices: Write clean, readable, and well-documented code. Adhere to established coding standards, such as PEP 8 for Python, to maintain consistency and readability. Comment your code appropriately to enhance its understandability and maintainability.
4. Test and Validate Your Code: Thoroughly test your code to ensure its correctness and robustness. Write unit tests and integration tests to cover different scenarios and edge cases. Validate your code against real-world data and compare the results with expected outcomes.
5. Use Version Control: Utilize the version control systems Git to manage your code changes. Fork the *openhdemg* repository to create a separate copy under your GitHub account. Make your code contributions in the forked repository by creating a new branch from the current branch used for the development of new features. This allows for easy review, collaboration, and integration of your code into the *openhdemg* project. When you're ready, submit your changes as pull requests from your forked repository to the corresponding branch in the *openhdemg* repository.
6. Engage in Code Reviews: Participate in code reviews and provide constructive feedback to your fellow contributors. Actively engage in discussions, address comments and suggestions, and iteratively improve your code based on the feedback received.
7. Document Your Contributions: Document your code changes, including any new features, modifications, or improvements. Update the project's documentation or relevant documentation files to reflect your contributions accurately.
8. Communicate and Collaborate: Join the [*openhdemg* community discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"} to connect with other developers and maintain open communication channels. Collaborate with the community by sharing ideas, seeking help, or contributing to ongoing discussions.
9. Respect Licensing and Intellectual Property: Ensure that your code contributions comply with the project's chosen license. Respect intellectual property rights and avoid incorporating copyrighted code or resources without proper authorization or licensing.

By following these guidelines, you can contribute effectively to the *openhdemg* project and help advance the field of HD-EMG analysis. Your code contributions will play a vital role in improving the framework, expanding its functionality, and enabling new research possibilities. Thank you for being a valuable member of our code development community!

## Specific guidelines for code developers

These guidelines should not be interpreted and must apply to all the developers. If you spot any divergence from these rules in the actual code, please suggest the author to edit the corresponding section.

- Language: British English
- Documentation style: NumPy
- Respect PEP 8
- Use a code checker (suggested flake8)
- Never alter the original structure of the emgfile described in the tutorial [Structure of the emgfile](/tutorials/emgfile_structure)
- Always work (i.e., Fetch/Pull request) on the current working branch. Not in the main branch.
