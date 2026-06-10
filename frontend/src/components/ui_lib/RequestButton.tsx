import * as React from "react";
import { createLink, LinkComponent } from "@tanstack/react-router";
import related from "@/assets/related.svg";

interface BasicLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  // Add any additional props you want to pass to the anchor element
}

const BasicLinkComponent = React.forwardRef<HTMLAnchorElement, BasicLinkProps>(
  (props, ref) => {
    return (
      <a
        ref={ref}
        {...props}
        className={"hover:bg-gray-50 rounded-[0.2rem] p-[0.4rem]"}
      >
        <img src={related} alt="go" />
      </a>
    );
  }
);

const CreatedLinkComponent = createLink(BasicLinkComponent);

const RequestButton: LinkComponent<typeof BasicLinkComponent> = (props) => {
  return <CreatedLinkComponent {...props} />;
};

export default RequestButton;
