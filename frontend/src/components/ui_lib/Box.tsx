interface BoxProps {
  children: React.ReactNode;
  className?: string;
}

export default function Box(props: BoxProps) {
  const box_names = " flex";
  const cls_name = props.className + box_names;
  return <div className={cls_name ?? ""}>{props.children}</div>;
}
